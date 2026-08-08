"""
Drift-Triggered Retraining
============================

Wires PSI drift detection to a real retrain, replacing the old behavior
where "drift detected" just routed traffic to a second, static,
pre-trained model with no relationship to the actual drift observed.

Design:
  - Retraining runs scripts/train.py as a subprocess, on a background
    thread, so it never blocks the request that triggered it. Training
    takes roughly a minute; the request that detected drift still gets
    served immediately by whichever model is currently loaded.
  - A cooldown prevents every drifted batch in a burst from spawning
    its own retrain -- only one retrain can be in flight/recently
    triggered at a time.
  - On success, the freshly retrained Champion + Challenger (already
    written to Models/*.pkl by train.py) are reloaded into the running
    server's memory immediately, so the very next request benefits.
  - Every step (triggered / completed / failed) is logged as a
    governance event, same as everything else in config.py.
"""
import os
import subprocess
import sys
import threading
import time

import config


def _run_retrain():
    config.log_governance_event(
        "RETRAIN_TRIGGERED",
        "PSI drift exceeded threshold -- starting scripts/train.py in the background.",
        "system",
    )
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    env = {**os.environ, "MPLBACKEND": "Agg"}

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, "scripts/train.py"],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except Exception as e:
        config.log_governance_event("RETRAIN_FAILED", f"Retrain subprocess error: {e}", "system")
        return

    elapsed = round(time.time() - start, 1)

    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-800:]
        config.log_governance_event(
            "RETRAIN_FAILED",
            f"Retrain subprocess exited {result.returncode} after {elapsed}s. Tail: {tail}",
            "system",
        )
        return

    # Reload the freshly retrained models into the running server
    from model_loader import load_model
    load_model()

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
            _run_retrain()
        finally:
            config.RETRAIN_IN_PROGRESS = False

    threading.Thread(target=_wrapped, daemon=True).start()
