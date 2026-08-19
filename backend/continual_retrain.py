"""
Growing-Window Retraining -- persists a training corpus that grows with
each real drift event, instead of retraining on the same static
application_train.csv snapshot every time.
=============================================================================

Context: continual_learning_demo.py proved (with synthetic "eras") that
growing-window retraining measurably recovers AUC after drift without
hurting general performance. This module wires that same mechanism into
the LIVE drift-triggered retrain path (retrain.py) -- with one honest
difference the demo didn't have to deal with: a real incoming batch that
triggers drift has no TARGET labels. It's live, unlabeled production
data -- the "label-lag problem" documented in docs/interview-prep.pdf
Part V (a real bank wouldn't know a new applicant's actual outcome for
months).

Rather than pretend the drifted batch itself is trainable, or silently
drop the growing-window idea once it leaves the demo, this generalizes
the demo's own method: resample real historical rows (with their real
TARGET labels intact) from the cumulative corpus, and shift their feature
values to match the REAL drift just observed -- calibrated from the
actual incoming batch vs. the baseline, not a fixed per-era demo
constant. Each synthesized row is a real label paired with feature values
reshaped to resemble what the live server is now actually seeing.

This is an explicit, disclosed proxy for labels the project does not
have -- never presented as real new outcomes. Every append is logged as a
CONTINUAL_ERA_APPENDED governance event so it's auditable, not a silent
background mutation of the training set.
"""
import os

import numpy as np
import pandas as pd

import config
from preprocessing import reshape_raw_kaggle_columns, engineer_champion_features

RAW_DATA_PATH = "dataset/raw/application_train.csv"
CUMULATIVE_DATA_PATH = "dataset/cumulative_training_data.csv"

# Same feature groups continual_learning_demo.py's synthetic era-shift
# transform uses, kept consistent so the live mechanism and the harness
# that proved it are directly comparable.
AMOUNT_COLS = ["AMT_INCOME_TOTAL", "AMT_CREDIT_x", "AMT_ANNUITY"]
EXT_SOURCE_COLS = ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]

# Caps how much one drift event can grow the corpus by -- a single large
# upload shouldn't be allowed to dwarf the original 307k-row dataset in
# one retrain cycle.
MAX_SYNTHETIC_ERA_ROWS = 5000
SHIFT_SCALE_BOUNDS = (0.5, 2.0)
SHIFT_OFFSET_BOUNDS = (-0.3, 0.3)


def get_training_data_path() -> str:
    """The growing-window training source: the persisted cumulative corpus
    once real drift has appended to it, else the original static dataset.
    Used by scripts/train.py so every retrain -- drift-triggered or
    manual -- benefits from whatever the corpus has grown to."""
    return CUMULATIVE_DATA_PATH if os.path.exists(CUMULATIVE_DATA_PATH) else RAW_DATA_PATH


def ensure_cumulative_corpus() -> str:
    """Seed the cumulative corpus from the static dataset the first time
    it's needed. Idempotent -- a no-op once the file already exists."""
    if not os.path.exists(CUMULATIVE_DATA_PATH):
        seed = pd.read_csv(RAW_DATA_PATH)
        seed.to_csv(CUMULATIVE_DATA_PATH, index=False)
        print(f"[continual] Seeded {CUMULATIVE_DATA_PATH} from {RAW_DATA_PATH} ({len(seed)} rows)")
    return CUMULATIVE_DATA_PATH


def _calibrate_shift(drifted_engineered: pd.DataFrame) -> dict:
    """Derive a distribution-shift calibration from the REAL drifted batch
    vs. the current baseline -- the same style of shift
    continual_learning_demo.py's ERA_SHIFTS hardcodes per simulated era,
    generalized here from an actual observed drift event instead of a
    fixed constant."""
    scale, offset = 1.0, 0.0
    baseline = config.BASELINE_DATA
    if baseline is None:
        return {"amount_scale": scale, "ext_source_shift": offset}

    ratios = []
    for col in AMOUNT_COLS:
        if col in drifted_engineered.columns and col in baseline.columns:
            b_med = baseline[col].median()
            d_med = drifted_engineered[col].median()
            if b_med and b_med > 0 and pd.notna(d_med):
                ratios.append(d_med / b_med)
    if ratios:
        scale = float(np.clip(np.mean(ratios), *SHIFT_SCALE_BOUNDS))

    offsets = []
    for col in EXT_SOURCE_COLS:
        if col in drifted_engineered.columns and col in baseline.columns:
            b_med = baseline[col].median()
            d_med = drifted_engineered[col].median()
            if pd.notna(b_med) and pd.notna(d_med):
                offsets.append(d_med - b_med)
    if offsets:
        offset = float(np.clip(np.mean(offsets), *SHIFT_OFFSET_BOUNDS))

    return {"amount_scale": scale, "ext_source_shift": offset}


def append_synthetic_era(drifted_raw_df: pd.DataFrame) -> dict:
    """Grow the persisted training corpus by one synthesized "era" calibrated
    from a real drift event, so the NEXT drift-triggered retrain trains on a
    larger, more representative window instead of the same static file.
    See the module docstring for why this resamples labeled historical rows
    rather than using the drifted batch's own (label-less) rows directly.
    """
    path = ensure_cumulative_corpus()

    drifted_engineered = engineer_champion_features(reshape_raw_kaggle_columns(drifted_raw_df))
    shift = _calibrate_shift(drifted_engineered)

    cumulative = pd.read_csv(path)
    n = min(len(drifted_raw_df), MAX_SYNTHETIC_ERA_ROWS, len(cumulative))
    synthetic_era = cumulative.sample(n=n, replace=False).copy()

    for col in AMOUNT_COLS:
        if col in synthetic_era.columns:
            synthetic_era[col] = synthetic_era[col] * shift["amount_scale"]
    for col in EXT_SOURCE_COLS:
        if col in synthetic_era.columns:
            synthetic_era[col] = (synthetic_era[col] + shift["ext_source_shift"]).clip(lower=0.0, upper=1.0)

    grown = pd.concat([cumulative, synthetic_era], ignore_index=True)
    grown.to_csv(path, index=False)

    summary = {
        "synthetic_rows_added": int(n),
        "cumulative_rows_after": int(len(grown)),
        "amount_scale_factor": round(shift["amount_scale"], 4),
        "ext_source_shift_factor": round(shift["ext_source_shift"], 4),
    }
    print(f"[continual] Appended synthetic era to {path}: {summary}")
    config.log_governance_event(
        "CONTINUAL_ERA_APPENDED",
        (
            f"Real drift observed -- resampled {n} historical rows (real TARGET "
            f"labels kept, feature values shifted: amount x{summary['amount_scale_factor']}, "
            f"ext_source {summary['ext_source_shift_factor']:+}) and appended to the "
            f"growing training corpus, now {summary['cumulative_rows_after']} rows. "
            f"This is a labeled proxy for the drifted population -- the real batch "
            f"itself has no TARGET labels available (label-lag problem)."
        ),
        "system",
    )
    return summary
