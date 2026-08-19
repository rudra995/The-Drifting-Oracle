"""
Tests for continual_retrain.py -- the growing-window training corpus.

Never touches the real dataset/raw/application_train.csv or the real
cumulative corpus; RAW_DATA_PATH/CUMULATIVE_DATA_PATH are monkeypatched to
small files under tmp_path for every test.
"""
import os

import pandas as pd
import pytest

import config
import continual_retrain as cr


def _seed_df(n=50, income=150000.0, ext=0.5):
    return pd.DataFrame({
        "SK_ID_CURR": range(n),
        "TARGET": [0, 1] * (n // 2),
        "AMT_INCOME_TOTAL": [income] * n,
        "AMT_CREDIT_x": [500000.0] * n,
        "AMT_ANNUITY": [25000.0] * n,
        "EXT_SOURCE_1": [ext] * n,
        "EXT_SOURCE_2": [ext] * n,
        "EXT_SOURCE_3": [ext] * n,
    })


@pytest.fixture
def paths(tmp_path, monkeypatch):
    raw_path = tmp_path / "application_train.csv"
    cumulative_path = tmp_path / "cumulative_training_data.csv"
    _seed_df().to_csv(raw_path, index=False)

    monkeypatch.setattr(cr, "RAW_DATA_PATH", str(raw_path))
    monkeypatch.setattr(cr, "CUMULATIVE_DATA_PATH", str(cumulative_path))
    monkeypatch.setattr(config, "BASELINE_DATA", None)
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
    seeded = pd.read_csv(cumulative_path)
    assert len(seeded) == 50

    # Idempotent -- calling again doesn't reseed or duplicate rows.
    cr.ensure_cumulative_corpus()
    assert len(pd.read_csv(cumulative_path)) == 50


def test_calibrate_shift_is_neutral_without_a_baseline(paths):
    drifted = _seed_df(n=10, income=300000.0, ext=0.9)
    shift = cr._calibrate_shift(drifted)
    assert shift == {"amount_scale": 1.0, "ext_source_shift": 0.0}


def test_calibrate_shift_reflects_a_real_observed_drift(paths, monkeypatch):
    baseline = _seed_df(n=50, income=150000.0, ext=0.5)
    monkeypatch.setattr(config, "BASELINE_DATA", baseline)

    # AMOUNT_COLS = [AMT_INCOME_TOTAL, AMT_CREDIT_x, AMT_ANNUITY]; only
    # income doubles here (credit/annuity held at _seed_df's defaults, same
    # as baseline) -- amount_scale is the MEAN ratio across all three, i.e.
    # (2.0 + 1.0 + 1.0) / 3. ext_source_shift changes all three EXT_SOURCE_*
    # columns uniformly, so its mean equals the per-column shift exactly.
    drifted = _seed_df(n=10, income=300000.0, ext=0.8)  # 2x income, +0.3 ext
    shift = cr._calibrate_shift(drifted)

    assert shift["amount_scale"] == pytest.approx(4 / 3, rel=1e-3)
    assert shift["ext_source_shift"] == pytest.approx(0.3, rel=1e-3)


def test_calibrate_shift_clips_extreme_ratios_to_bounds(paths, monkeypatch):
    baseline = _seed_df(n=50, income=150000.0, ext=0.1)
    monkeypatch.setattr(config, "BASELINE_DATA", baseline)

    drifted = _seed_df(n=10, income=150000.0 * 10, ext=0.99)
    shift = cr._calibrate_shift(drifted)

    assert shift["amount_scale"] == cr.SHIFT_SCALE_BOUNDS[1]
    assert shift["ext_source_shift"] == cr.SHIFT_OFFSET_BOUNDS[1]


def test_append_synthetic_era_grows_corpus_and_preserves_real_labels(paths, monkeypatch):
    raw_path, cumulative_path = paths
    baseline = _seed_df(n=50, income=150000.0, ext=0.5)
    monkeypatch.setattr(config, "BASELINE_DATA", baseline)
    monkeypatch.setattr(config, "log_governance_event", lambda *a, **kw: None)

    drifted_batch = _seed_df(n=20, income=225000.0, ext=0.65)
    summary = cr.append_synthetic_era(drifted_batch)

    grown = pd.read_csv(cumulative_path)
    assert len(grown) == 50 + summary["synthetic_rows_added"]
    assert summary["cumulative_rows_after"] == len(grown)
    # Real TARGET labels only ever come from the original 0/1 seed values --
    # the shift transform never touches TARGET, so no new label values appear.
    assert set(grown["TARGET"].unique()) <= {0, 1}


def test_append_synthetic_era_caps_rows_added_at_max(paths, monkeypatch):
    monkeypatch.setattr(config, "BASELINE_DATA", None)
    monkeypatch.setattr(config, "log_governance_event", lambda *a, **kw: None)
    monkeypatch.setattr(cr, "MAX_SYNTHETIC_ERA_ROWS", 5)

    drifted_batch = _seed_df(n=1000)
    summary = cr.append_synthetic_era(drifted_batch)

    assert summary["synthetic_rows_added"] == 5
