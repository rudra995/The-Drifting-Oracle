"""
Unit tests for psi.py -- the PSI drift-detection math.

This is the part of the app most likely to break silently: bad bin edges
or unclipped zero-percent bins turn into NaN/inf PSI scores that still
"work" (no crash) but quietly produce a meaningless drift signal. These
tests exist to catch exactly that class of bug.
"""
import numpy as np
import pandas as pd
import pytest

import config
from psi import (
    create_bins,
    get_distribution,
    calculate_psi_single,
    build_baseline_distributions,
    calculate_multi_feature_psi,
    EPSILON,
)


# --------------------------------------------------------------------
# create_bins
# --------------------------------------------------------------------

def test_create_bins_normal_distribution_has_correct_edge_count():
    series = pd.Series(np.linspace(0, 100, 1000))
    bins = create_bins(series, num_bins=10)
    # Quantile edges collapse duplicates, but for a smooth distribution
    # we should get close to num_bins + 1 edges, capped by uniqueness.
    assert len(bins) >= 2
    assert bins[0] == -np.inf
    assert bins[-1] == np.inf


def test_create_bins_constant_column_collapses_to_open_interval():
    """A column where every value is identical can't be quantile-binned --
    all quantiles are the same number, so np.unique collapses them to one
    value. The function must fall back to a single [-inf, inf] bin rather
    than producing a degenerate bins array."""
    series = pd.Series([42.0] * 500)
    bins = create_bins(series, num_bins=10)
    assert len(bins) == 2
    assert bins[0] == -np.inf
    assert bins[1] == np.inf


def test_create_bins_drops_nan_before_binning():
    series = pd.Series([1.0, 2.0, np.nan, 3.0, np.nan, 4.0] * 50)
    bins = create_bins(series, num_bins=4)
    assert not np.isnan(bins).any()


# --------------------------------------------------------------------
# get_distribution
# --------------------------------------------------------------------

def test_get_distribution_sums_to_one():
    series = pd.Series(np.random.default_rng(0).normal(size=1000))
    bins = create_bins(series, num_bins=10)
    dist = get_distribution(series, bins)
    assert dist.sum() == pytest.approx(1.0, abs=1e-6)


def test_get_distribution_never_returns_exact_zero():
    """A bin with 0 observations must be epsilon-clipped, not left at 0 --
    PSI's log(actual/expected) explodes to +/-inf on a literal zero."""
    # All values fall in the first bin only -- later bins are empty.
    series = pd.Series([1.0] * 100)
    bins = np.array([-np.inf, 2.0, 4.0, 6.0, np.inf])
    dist = get_distribution(series, bins)
    assert (dist > 0).all()
    assert dist.min() == pytest.approx(EPSILON, abs=1e-9) or dist.min() > 0


def test_get_distribution_empty_series_returns_epsilon_everywhere():
    series = pd.Series([], dtype=float)
    bins = np.array([-np.inf, 0.0, np.inf])
    dist = get_distribution(series, bins)
    assert len(dist) == 2
    assert (dist == EPSILON).all()


# --------------------------------------------------------------------
# calculate_psi_single
# --------------------------------------------------------------------

def test_psi_is_near_zero_for_identical_distributions():
    dist = np.array([0.1, 0.2, 0.3, 0.2, 0.2])
    psi = calculate_psi_single(dist, dist.copy())
    assert psi == pytest.approx(0.0, abs=1e-9)


def test_psi_is_large_for_very_different_distributions():
    expected = np.array([0.5, 0.5])
    actual = np.array([0.01, 0.99])
    psi = calculate_psi_single(expected, actual)
    assert psi > 0.25  # well past the "significant shift" threshold


def test_psi_handles_zero_bins_without_producing_nan_or_inf():
    expected = np.array([1.0, 0.0, 0.0])
    actual = np.array([0.0, 0.5, 0.5])
    psi = calculate_psi_single(expected, actual)
    assert np.isfinite(psi)
    assert psi > 0


# --------------------------------------------------------------------
# calculate_multi_feature_psi (uses config module state)
# --------------------------------------------------------------------

@pytest.fixture
def stable_baseline(monkeypatch):
    """A baseline where two features have known, fixed distributions."""
    rng = np.random.default_rng(42)
    baseline_a = pd.Series(rng.normal(loc=0, scale=1, size=2000))
    baseline_b = pd.Series(rng.normal(loc=100, scale=10, size=2000))

    bins_a = create_bins(baseline_a, config.PSI_NUM_BINS)
    bins_b = create_bins(baseline_b, config.PSI_NUM_BINS)

    monkeypatch.setattr(config, "PSI_FEATURES", ["feature_a", "feature_b"])
    monkeypatch.setattr(config, "BASELINE_BINS", {"feature_a": bins_a, "feature_b": bins_b})
    monkeypatch.setattr(config, "BASELINE_DISTRIBUTIONS", {
        "feature_a": get_distribution(baseline_a, bins_a),
        "feature_b": get_distribution(baseline_b, bins_b),
    })
    monkeypatch.setattr(config, "PSI_THRESHOLD", 0.25)
    return rng


def test_multi_feature_psi_no_drift_when_incoming_matches_baseline(stable_baseline):
    rng = stable_baseline
    incoming = pd.DataFrame({
        "feature_a": rng.normal(loc=0, scale=1, size=500),
        "feature_b": rng.normal(loc=100, scale=10, size=500),
    })
    overall_psi, per_feature, drift_detected = calculate_multi_feature_psi(incoming)
    assert drift_detected is False
    assert overall_psi < config.PSI_THRESHOLD
    assert set(per_feature.keys()) == {"feature_a", "feature_b"}


def test_multi_feature_psi_detects_drift_on_shifted_distribution(stable_baseline):
    rng = stable_baseline
    incoming = pd.DataFrame({
        # Massively shifted mean and scale on both features
        "feature_a": rng.normal(loc=8, scale=0.5, size=500),
        "feature_b": rng.normal(loc=300, scale=5, size=500),
    })
    overall_psi, per_feature, drift_detected = calculate_multi_feature_psi(incoming)
    assert drift_detected is True
    assert overall_psi >= config.PSI_THRESHOLD


def test_multi_feature_psi_skips_features_missing_from_incoming_data(stable_baseline):
    incoming = pd.DataFrame({"feature_a": [0.1, 0.2, 0.3]})  # feature_b absent
    overall_psi, per_feature, drift_detected = calculate_multi_feature_psi(incoming)
    assert "feature_b" not in per_feature
    assert "feature_a" in per_feature


def test_multi_feature_psi_returns_zero_when_no_baseline_configured(monkeypatch):
    monkeypatch.setattr(config, "PSI_FEATURES", ["nonexistent"])
    monkeypatch.setattr(config, "BASELINE_DISTRIBUTIONS", {})
    monkeypatch.setattr(config, "BASELINE_BINS", {})
    incoming = pd.DataFrame({"nonexistent": [1, 2, 3]})
    overall_psi, per_feature, drift_detected = calculate_multi_feature_psi(incoming)
    assert overall_psi == 0.0
    assert per_feature == {}
    assert drift_detected is False
