"""
Tests for continual_retrain.py -- the growing-window training corpus,
grown via k-NN matching against a real drifted batch (see the module
docstring for why: real drift has no labels, so this borrows the label of
each drifted row's nearest historical neighbor instead).

Never touches the real dataset/raw/application_train.csv or the real
cumulative corpus; RAW_DATA_PATH/CUMULATIVE_DATA_PATH are monkeypatched to
small files under tmp_path for every test.
"""
import os

import pandas as pd
import pytest

import config
import continual_retrain as cr

# Two well-separated clusters so a k-NN match is verifiable: "low" (small
# income/credit, low EXT_SOURCE scores, TARGET=0) and "high" (large
# income/credit, high EXT_SOURCE scores, TARGET=1). A query row that looks
# like "high" should only ever match "high" rows, never "low" ones.
LOW = dict(AMT_INCOME_TOTAL=50000.0, AMT_CREDIT_x=100000.0, AMT_ANNUITY=5000.0,
           DAYS_EMPLOYED=-500, EXT_SOURCE_2=0.15, EXT_SOURCE_3=0.15)
HIGH = dict(AMT_INCOME_TOTAL=500000.0, AMT_CREDIT_x=1000000.0, AMT_ANNUITY=50000.0,
            DAYS_EMPLOYED=-3000, EXT_SOURCE_2=0.85, EXT_SOURCE_3=0.85)


def _cluster_df(n, base, target, ext3_nan_frac=0.0, start_id=0):
    rows = []
    for i in range(n):
        row = dict(base)
        row["SK_ID_CURR"] = start_id + i
        row["TARGET"] = target
        # Small jitter so rows aren't all identical, still tightly clustered.
        row["AMT_INCOME_TOTAL"] += i
        rows.append(row)
    df = pd.DataFrame(rows)
    if ext3_nan_frac:
        n_nan = int(len(df) * ext3_nan_frac)
        df.loc[df.index[:n_nan], "EXT_SOURCE_3"] = float("nan")
    return df


def _seed_corpus(n_low=100, n_high=100, ext3_nan_frac=0.0):
    low = _cluster_df(n_low, LOW, target=0, ext3_nan_frac=ext3_nan_frac, start_id=0)
    high = _cluster_df(n_high, HIGH, target=1, ext3_nan_frac=ext3_nan_frac, start_id=n_low)
    return pd.concat([low, high], ignore_index=True)


@pytest.fixture
def paths(tmp_path, monkeypatch):
    raw_path = tmp_path / "application_train.csv"
    cumulative_path = tmp_path / "cumulative_training_data.csv"
    _seed_corpus().to_csv(raw_path, index=False)

    monkeypatch.setattr(cr, "RAW_DATA_PATH", str(raw_path))
    monkeypatch.setattr(cr, "CUMULATIVE_DATA_PATH", str(cumulative_path))
    monkeypatch.setattr(config, "log_governance_event", lambda *a, **kw: None)
    return raw_path, cumulative_path


def test_get_training_data_path_falls_back_to_raw_until_grown(paths):
    raw_path, cumulative_path = paths
    assert cr.get_training_data_path() == str(raw_path)

    cr.ensure_cumulative_corpus()
    assert cr.get_training_data_path() == str(cumulative_path)


def test_ensure_cumulative_corpus_seeds_once(paths):
    raw_path, cumulative_path = paths
    cr.ensure_cumulative_corpus()
    assert os.path.exists(cumulative_path)
    assert len(pd.read_csv(cumulative_path)) == 200

    cr.ensure_cumulative_corpus()  # idempotent
    assert len(pd.read_csv(cumulative_path)) == 200


def test_nearest_historical_rows_matches_the_correct_cluster(paths):
    cr.ensure_cumulative_corpus()
    cumulative_raw = _seed_corpus()
    from preprocessing import reshape_raw_kaggle_columns, engineer_champion_features
    cumulative_engineered = engineer_champion_features(reshape_raw_kaggle_columns(cumulative_raw))

    drifted_batch = _cluster_df(10, HIGH, target=None, start_id=999)
    drifted_engineered = engineer_champion_features(reshape_raw_kaggle_columns(drifted_batch))

    matched = cr._nearest_historical_rows(drifted_engineered, cumulative_engineered, cumulative_raw, n=10)

    assert len(matched) == 10
    # Every match must be a real "high" cluster row -- both its label and
    # its untouched original feature values.
    assert (matched["TARGET"] == 1).all()
    assert (matched["AMT_INCOME_TOTAL"] >= 400000).all()


def test_nearest_historical_rows_handles_missing_ext_source_3(paths):
    cr.ensure_cumulative_corpus()
    cumulative_raw = _seed_corpus(ext3_nan_frac=0.3)
    from preprocessing import reshape_raw_kaggle_columns, engineer_champion_features
    cumulative_engineered = engineer_champion_features(reshape_raw_kaggle_columns(cumulative_raw))

    drifted_batch = _cluster_df(5, LOW, target=None, start_id=999)
    drifted_engineered = engineer_champion_features(reshape_raw_kaggle_columns(drifted_batch))

    matched = cr._nearest_historical_rows(drifted_engineered, cumulative_engineered, cumulative_raw, n=5)

    assert len(matched) == 5
    assert (matched["TARGET"] == 0).all()
    # Matched candidates were drawn only from EXT_SOURCE_3-complete rows.
    assert matched["EXT_SOURCE_3"].notna().all()


def test_nearest_historical_rows_falls_back_without_feature_overlap(paths, monkeypatch):
    monkeypatch.setattr(config, "PSI_FEATURES", ["totally_unrelated_column"])
    cumulative_raw = _seed_corpus()
    empty_engineered = pd.DataFrame(index=cumulative_raw.index)
    drifted_engineered = pd.DataFrame(index=range(5))

    matched = cr._nearest_historical_rows(drifted_engineered, empty_engineered, cumulative_raw, n=5)
    assert len(matched) == 5  # random-sample fallback, not a crash


def test_append_synthetic_era_grows_corpus_and_preserves_real_rows(paths):
    raw_path, cumulative_path = paths
    drifted_batch = _cluster_df(20, HIGH, target=None, start_id=999)

    summary = cr.append_synthetic_era(drifted_batch)

    grown = pd.read_csv(cumulative_path)
    assert len(grown) == 200 + summary["synthetic_rows_added"]
    assert summary["cumulative_rows_after"] == len(grown)
    # Matched rows are real, untouched historical rows -- only real labels.
    assert set(grown["TARGET"].unique()) <= {0, 1}
    # Every original column survives (matched rows are whole originals, no
    # partial/synthesized columns to drop or misalign).
    assert set(grown.columns) == set(_seed_corpus().columns)


def test_append_synthetic_era_caps_rows_added_at_max(paths, monkeypatch):
    monkeypatch.setattr(cr, "MAX_SYNTHETIC_ERA_ROWS", 5)
    drifted_batch = _cluster_df(50, HIGH, target=None, start_id=999)

    summary = cr.append_synthetic_era(drifted_batch)

    assert summary["synthetic_rows_added"] == 5
