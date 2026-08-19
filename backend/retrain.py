"""
Drift-Triggered Retraining -- orchestrated as a Prefect flow
===============================================================

Wires PSI drift detection to a real retrain, replacing the old behavior
where "drift detected" just routed traffic to a second, static,
pre-trained model with no relationship to the actual drift observed.

Design:
  - The actual training work runs inside a Prefect flow (`retrain_flow`),
    not as a bare subprocess call inline in predict_batch()'s request
    handler. Wrapping it as a flow (with the subprocess call as its own
    @task) gets three things a plain function call doesn't: automatic
    retries on a transient failure, a structured, timestamped run log
    independent of print(), and a named, inspectable unit of work instead
    of an untraceable side effect of an HTTP request.
  - maybe_trigger_retrain() keeps the request-path throttling (cooldown +
    in-progress guard) -- that's application-level rate limiting, not
    orchestration, so it stays outside the flow. It runs the flow on a
    background thread so the request that detected drift is never
    blocked; training takes a few minutes, and that request still gets
    served immediately by whichever model is currently loaded.
  - No standalone Prefect server/worker is deployed for this -- calling
    the flow directly uses Prefect's local ephemeral engine, which still
    gives task-level retries and a queryable run history (local SQLite
    under ~/.prefect/), consistent with the project's zero-cost
    constraint. A real deployment (`prefect deploy` + a worker) is a
    drop-in upgrade path, not a rewrite, if this ever needs a schedule or
    a UI dashboard beyond flow-run logs.
  - On flow success, the freshly retrained Champion + Challenger (already
    written to Models/*.pkl by train.py) are reloaded into the running
    server's memory immediately, so the very next request benefits.
  - Every step (triggered / completed / failed) is still logged as a
    governance event in Delta, same as everything else in config.py --
    Prefect's own run logs complement that, they don't replace it.
"""
import os
import subprocess
import sys
import threading
import time

import pandas as pd
from prefect import flow, task, get_run_logger

import config


@task(name="run-train-script", retries=2, retry_delay_seconds=30, log_prints=True)
def run_training_subprocess() -> str:
    """Run scripts/train.py as a subprocess and return its tail output.

    Raises on a non-zero exit so Prefect's task-level retry can recover
    from a transient failure (e.g. a momentarily unreachable Databricks
    workspace) instead of the whole flow failing on the first bad
    attempt.
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    env = {**os.environ, "MPLBACKEND": "Agg"}

    result = subprocess.run(
        [sys.executable, "scripts/train.py"],
        cwd=backend_dir,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-800:]
        raise RuntimeError(f"train.py exited {result.returncode}. Tail: {tail}")

    print(result.stdout[-800:])
    return result.stdout[-800:]


@task(name="tune-decision-threshold", retries=1, retry_delay_seconds=15, log_prints=True)
def run_threshold_tuning_subprocess() -> str:
    """Run scripts/tune_threshold.py against the freshly retrained Champion.

    A retrained model's optimal decision threshold isn't necessarily the
    same as the previous model's -- without this task, every retrain was
    silently overwriting Models/model_metrics.json (via train.py's
    write_local_metrics) and wiping out champion.decision_threshold, since
    train.py has no knowledge of it. Re-tuning on every retrain keeps the
    threshold and the model it applies to always in sync, rather than a
    one-time script run that quietly goes stale on the next drift event.
    A failure here is non-fatal to the retrain overall (best-effort,
    retries=1) -- config.get_decision_threshold() falls back to 0.5 if the
    field is ever missing, so a tuning failure degrades gracefully rather
    than blocking the retrain/reload the drift alert actually needs.
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        [sys.executable, "scripts/tune_threshold.py"],
        cwd=backend_dir,
        env={**os.environ, "MPLBACKEND": "Agg"},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-800:]
        raise RuntimeError(f"tune_threshold.py exited {result.returncode}. Tail: {tail}")
    print(result.stdout[-800:])
    return result.stdout[-800:]


@task(name="reload-model-into-server")
def reload_model_task():
    """Hot-reload the freshly retrained Champion + Challenger (and its
    freshly re-tuned decision threshold) into the running server's memory."""
    from model_loader import load_model
    load_model()


@flow(name="drift-triggered-retrain", log_prints=True)
def retrain_flow():
    """Orchestrates the full drift -> retrain -> hot-reload pipeline as a
    single, retriable, observable Prefect flow run."""
    logger = get_run_logger()
    config.log_governance_event(
        "RETRAIN_TRIGGERED",
        "PSI drift exceeded threshold -- starting the drift-triggered-retrain Prefect flow.",
        "system",
    )

    start = time.time()
    try:
        run_training_subprocess()
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        logger.error(f"drift-triggered-retrain failed after {elapsed}s (all retries exhausted): {e}")
        config.log_governance_event(
            "RETRAIN_FAILED",
            f"Retrain flow failed after {elapsed}s (all retries exhausted): {e}",
            "system",
        )
        raise

    try:
        run_threshold_tuning_subprocess()
    except Exception as e:
        # Best-effort -- train.py has already overwritten model_metrics.json
        # without a decision_threshold field by this point regardless, so a
        # tuning failure here means config.get_decision_threshold() will
        # fall back to its 0.5 default until the next successful retrain,
        # not that a stale threshold is preserved.
        logger.warning(f"Decision-threshold tuning failed, falling back to the 0.5 default: {e}")

    reload_model_task()

    elapsed = round(time.time() - start, 1)
    logger.info(f"drift-triggered-retrain completed in {elapsed}s.")
    config.log_governance_event(
        "RETRAIN_COMPLETE",
        f"Retrain finished in {elapsed}s and reloaded into the running server. "
        f"Champion + Challenger both refreshed against the latest labeled data.",
        "system",
    )


def maybe_trigger_retrain(drifted_df: pd.DataFrame = None):
    """Call when drift is detected. No-op if a retrain was already triggered
    within the cooldown window, or one is currently running.

    drifted_df, if given, is the raw batch that triggered this drift alert.
    It's used to grow the training corpus (see continual_retrain.py) before
    the retrain itself runs, so the retrain benefits from the larger
    window on the same pass -- not deferred to the retrain after next.
    """
    now = time.time()
    if config.RETRAIN_IN_PROGRESS:
        return
    if now - config.LAST_RETRAIN_TRIGGERED_AT < config.RETRAIN_COOLDOWN_SECONDS:
        return

    config.LAST_RETRAIN_TRIGGERED_AT = now
    config.RETRAIN_IN_PROGRESS = True

    def _wrapped():
        try:
            if drifted_df is not None:
                try:
                    import continual_retrain
                    continual_retrain.append_synthetic_era(drifted_df)
                except Exception as e:
                    # Best-effort -- growing the corpus is an enhancement to
                    # the retrain, not a precondition for it. A failure here
                    # falls back to retraining on whatever the corpus
                    # already was (or the static dataset), same as before
                    # this mechanism existed.
                    print(f"[continual] Failed to append synthetic era, retraining without growing the corpus: {e}")
            retrain_flow()
        except Exception:
            pass  # already logged as RETRAIN_FAILED inside the flow
        finally:
            config.RETRAIN_IN_PROGRESS = False

    threading.Thread(target=_wrapped, daemon=True).start()
