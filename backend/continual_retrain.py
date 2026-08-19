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

Rather than pretend the drifted batch itself is trainable, this borrows
labels via k-NN matching: for every row in the real drifted batch, find
its single nearest neighbor in the historical corpus (Euclidean distance
over the same standardized PSI_FEATURES config.py already uses to DETECT
drift -- reusing that feature space, rather than inventing a second one,
keeps "what counts as similar" consistent between detection and
retraining) and pull that WHOLE historical row -- real features, real
TARGET label, every original column -- into the growing corpus, unmodified.

This replaced an earlier version that resampled RANDOM historical rows
and shifted a couple of features by one blanket scale/offset per drift
event. That approach corrupted correlation structure (a uniform shift
can't express "high earners specifically got riskier", only "everyone's
income went up") and needed hand-tuned clipping bounds. Nearest-neighbor
matching selects the historical rows that were ALREADY most similar to
the real observed drift instead of transforming random ones to
approximate it -- no shift math, no schema risk (matched rows are
untouched originals from the corpus, so every column stays consistent),
and it's a cheap proxy for the more principled (and much heavier)
density-ratio/importance-weighting approach: rows that keep getting
matched as "most similar to recent drift" effectively get upweighted in
the corpus by duplication, the same way importance weighting would
upweight them by a continuous factor.

This is still an explicit, disclosed proxy for labels the project does
not have -- a matched row's label is a real historical outcome, not a
real outcome for the applicant it was matched to. Every append is logged
as a CONTINUAL_ERA_APPENDED governance event so it's auditable, not a
silent background mutation of the training set.
"""
import os

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

import config
from preprocessing import reshape_raw_kaggle_columns, engineer_champion_features

RAW_DATA_PATH = "dataset/raw/application_train.csv"
CUMULATIVE_DATA_PATH = "dataset/cumulative_training_data.csv"

# Caps how much one drift event can grow the corpus by -- a single large
# upload shouldn't be allowed to dwarf the original 307k-row dataset in
# one retrain cycle.
MAX_SYNTHETIC_ERA_ROWS = 5000


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


def _nearest_historical_rows(
    drifted_engineered: pd.DataFrame,
    cumulative_engineered: pd.DataFrame,
    cumulative_raw: pd.DataFrame,
    n: int,
) -> pd.DataFrame:
    """For up to `n` rows of the real drifted batch, find each one's single
    nearest neighbor in the historical corpus (standardized Euclidean
    distance over config.PSI_FEATURES) and return the corresponding WHOLE
    original rows from cumulative_raw -- unmodified, real features, real
    TARGET labels, every column intact. Duplicate matches are allowed and
    expected (see module docstring: this is how "similar rows get
    upweighted" falls out of plain nearest-neighbor selection).

    NearestNeighbors can't handle NaN, so rows with a NaN in any matching
    feature (e.g. the ~20% of rows with a genuinely missing EXT_SOURCE_3)
    are dropped from the CANDIDATE pool -- there are always tens of
    thousands of complete candidates left at this project's scale, so this
    never meaningfully narrows what a query row can match. A query row's
    own NaNs are median-filled so a distance can be computed at all; that
    fill never touches what gets stored, since only the matched candidate
    row (already complete) is ever appended.
    """
    feature_cols = [c for c in config.PSI_FEATURES if c in drifted_engineered.columns and c in cumulative_engineered.columns]
    if not feature_cols:
        # No usable feature overlap (e.g. a baseline/engineered-feature
        # mismatch) -- fall back to plain random sampling rather than
        # failing the whole retrain over a degenerate edge case.
        return cumulative_raw.sample(n=min(n, len(cumulative_raw)), replace=False)

    candidates_mask = cumulative_engineered[feature_cols].notna().all(axis=1)
    candidates = cumulative_engineered.loc[candidates_mask, feature_cols]
    if candidates.empty:
        return cumulative_raw.sample(n=min(n, len(cumulative_raw)), replace=False)

    query = drifted_engineered[feature_cols].copy()
    query = query.fillna(candidates.median())

    scaler = StandardScaler()
    candidates_scaled = scaler.fit_transform(candidates)
    query_scaled = scaler.transform(query)

    n = min(n, len(query))
    nn = NearestNeighbors(n_neighbors=1).fit(candidates_scaled)
    _, neighbor_positions = nn.kneighbors(query_scaled[:n])

    # neighbor_positions indexes into `candidates` (post-dropna); map back
    # to the original cumulative_raw row labels the candidate pool kept.
    matched_labels = candidates.index[neighbor_positions.ravel()]
    return cumulative_raw.loc[matched_labels]


def append_synthetic_era(drifted_raw_df: pd.DataFrame) -> dict:
    """Grow the persisted training corpus with the historical rows nearest
    to a real drift event, so the NEXT drift-triggered retrain trains on a
    larger, more representative window instead of the same static file.
    See the module docstring for why this borrows labels via k-NN matching
    rather than using the drifted batch's own (label-less) rows directly.
    """
    path = ensure_cumulative_corpus()

    cumulative_raw = pd.read_csv(path)
    cumulative_engineered = engineer_champion_features(reshape_raw_kaggle_columns(cumulative_raw))
    drifted_engineered = engineer_champion_features(reshape_raw_kaggle_columns(drifted_raw_df))

    n = min(len(drifted_raw_df), MAX_SYNTHETIC_ERA_ROWS, len(cumulative_raw))
    matched_era = _nearest_historical_rows(drifted_engineered, cumulative_engineered, cumulative_raw, n)

    grown = pd.concat([cumulative_raw, matched_era], ignore_index=True)
    grown.to_csv(path, index=False)

    summary = {
        "synthetic_rows_added": int(len(matched_era)),
        "cumulative_rows_after": int(len(grown)),
        "unique_rows_matched": int(matched_era.index.nunique()),
    }
    print(f"[continual] Appended k-NN-matched era to {path}: {summary}")
    config.log_governance_event(
        "CONTINUAL_ERA_APPENDED",
        (
            f"Real drift observed -- matched {summary['synthetic_rows_added']} rows of the "
            f"drifted batch to their nearest historical neighbors ({summary['unique_rows_matched']} "
            f"distinct rows, real TARGET labels, unmodified) and appended them to the growing "
            f"training corpus, now {summary['cumulative_rows_after']} rows. This is a labeled "
            f"proxy for the drifted population -- the real batch itself has no TARGET labels "
            f"available (label-lag problem)."
        ),
        "system",
    )
    return summary
