"""
PSI (Population Stability Index) -- Multi-Feature Drift Detection
================================================================

Compares incoming CSV data against the champion model's training
distribution across >=5 key numeric features.

PSI formula per feature:
    PSI =  (Actual%  Expected%)  ln(Actual% / Expected%)

Overall PSI = mean of per-feature PSI values.

Thresholds:
    PSI < 0.25  -> Use Champion model (stable)
    PSI >= 0.25 -> Switch to Challenger model (drift detected)
"""
import numpy as np
import pandas as pd
import config

# Small constant to prevent log(0) and division-by-zero
EPSILON = 1e-6


def create_bins(data_series: pd.Series, num_bins: int) -> np.ndarray:
    """
    Create quantile-based bin edges from a baseline data column.
    
    Uses percentile-based binning to handle skewed distributions.
    Bin edges are fixed once computed -- incoming data is bucketed
    into the same bins for comparison.
    """
    quantiles = np.linspace(0, 1, num_bins + 1)
    bins = np.quantile(data_series.dropna(), quantiles)

    # Remove duplicate edges from heavily skewed distributions
    bins = np.unique(bins)

    if len(bins) > 1:
        bins[0] = -np.inf   # Catch all values below minimum
        bins[-1] = np.inf   # Catch all values above maximum
    else:
        bins = np.array([-np.inf, np.inf])

    return bins


def get_distribution(data_series: pd.Series, bin_edges: np.ndarray) -> np.ndarray:
    """
    Compute percentage distribution of data across fixed bins.
    
    Epsilon-clipping ensures no bin has exactly 0%, which would
    cause log(0) -> inf in the PSI formula.
    """
    counts, _ = np.histogram(data_series.dropna(), bins=bin_edges)
    total = counts.sum()

    if total == 0:
        return np.full(len(counts), EPSILON)

    percents = counts / total
    percents = np.clip(percents, EPSILON, 1.0)
    return percents


def calculate_psi_single(expected: np.ndarray, actual: np.ndarray) -> float:
    """
    Compute PSI between two pre-computed distributions.
    
    PSI =  (Actual_i  Expected_i)  ln(Actual_i / Expected_i)
    
    Both arrays must be epsilon-clipped to avoid numerical issues.
    """
    expected = np.clip(expected, EPSILON, 1.0)
    actual = np.clip(actual, EPSILON, 1.0)
    psi_values = (actual - expected) * np.log(actual / expected)
    return float(np.sum(psi_values))


def build_baseline_distributions(baseline_df: pd.DataFrame) -> None:
    """
    Pre-compute bin edges and distributions for each PSI feature
    from the training baseline. Called once at startup.
    
    Stores results in config.BASELINE_BINS and config.BASELINE_DISTRIBUTIONS.
    """
    for feature in config.PSI_FEATURES:
        if feature not in baseline_df.columns:
            print(f"[PSI] Warning: baseline missing feature '{feature}', skipping.")
            continue

        series = baseline_df[feature].dropna()
        if len(series) < 30:
            print(f"[PSI] Warning: insufficient baseline data for '{feature}' ({len(series)} rows), skipping.")
            continue

        bins = create_bins(series, config.PSI_NUM_BINS)
        dist = get_distribution(series, bins)

        config.BASELINE_BINS[feature] = bins
        config.BASELINE_DISTRIBUTIONS[feature] = dist

    print(f"[PSI] Baseline distributions computed for {len(config.BASELINE_DISTRIBUTIONS)} features: "
          f"{list(config.BASELINE_DISTRIBUTIONS.keys())}")


def calculate_multi_feature_psi(incoming_df: pd.DataFrame) -> tuple[float, dict, bool]:
    """
    Compare incoming CSV data against stored baseline distributions
    across all configured PSI features.
    
    Returns:
        overall_psi:   float -- average PSI across all features
        per_feature:   dict  -- {feature_name: psi_score}
        drift_detected: bool -- True if overall_psi >= PSI_THRESHOLD
    
    This is the CORE drift detection function. It compares DATA
    distributions, NOT models. Each feature's PSI measures how much
    the incoming batch's distribution has shifted from the training set.
    """
    per_feature = {}

    for feature in config.PSI_FEATURES:
        # Skip features that weren't in baseline or incoming data
        if feature not in config.BASELINE_DISTRIBUTIONS:
            continue
        if feature not in incoming_df.columns:
            continue

        baseline_dist = config.BASELINE_DISTRIBUTIONS[feature]
        baseline_bins = config.BASELINE_BINS[feature]

        # Compute distribution of the incoming data using the SAME bin edges
        incoming_series = incoming_df[feature].dropna()
        if len(incoming_series) == 0:
            continue

        incoming_dist = get_distribution(incoming_series, baseline_bins)

        # Per-feature PSI
        psi = calculate_psi_single(baseline_dist, incoming_dist)
        per_feature[feature] = round(psi, 4)

    # Overall PSI = average across features
    if per_feature:
        overall_psi = round(sum(per_feature.values()) / len(per_feature), 4)
    else:
        overall_psi = 0.0

    # Drift decision: strict threshold at 0.25
    drift_detected = overall_psi >= config.PSI_THRESHOLD

    print(f"[PSI] Overall PSI = {overall_psi} | Drift = {drift_detected}")
    for feat, score in per_feature.items():
        print(f"  -> {feat}: {score}")

    return overall_psi, per_feature, drift_detected
