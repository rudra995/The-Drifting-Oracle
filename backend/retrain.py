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


@task(name="reload-model-into-server")
def reload_model_task():
    """Hot-reload the freshly retrained Champion + Challenger into the
    running server's memory."""
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

    reload_model_task()

    elapsed = round(time.time() - start, 1)
    logger.info(f"drift-triggered-retrain completed in {elapsed}s.")
    config.log_governance_event(
        "RETRAIN_COMPLETE",
        f"Retrain finished in {elapsed}s and reloaded into the running server. "
        f"Champion + Challenger both refreshed against the latest labeled data.",
        "system",
    )


def maybe_trigger_retrain():
    """Call when drift is detected. No-op if a retrain was already triggered
    within the cooldown window, or one is currently running."""
    now = time.time()
    if config.RETRAIN_IN_PROGRESS:
        return
    if now - config.LAST_RETRAIN_TRIGGERED_AT < config.RETRAIN_COOLDOWN_SECONDS:
        return

    config.LAST_RETRAIN_TRIGGERED_AT = now
    config.RETRAIN_IN_PROGRESS = True

    def _wrapped():
        try:
            retrain_flow()
        except Exception:
            pass  # already logged as RETRAIN_FAILED inside the flow
        finally:
            config.RETRAIN_IN_PROGRESS = False

    threading.Thread(target=_wrapped, daemon=True).start()
