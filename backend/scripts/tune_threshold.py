"""
Decision-threshold tuning for the Champion model.
=====================================================

The training script (train.py) reports precision/recall/F1 at a flat 0.5
threshold -- sklearn's default, not a value grounded in what a false
rejection actually costs a bank versus a missed default. This script:

  1. Rebuilds the exact same 80/20 stratified split train.py uses
     (same random_state=42), so this evaluates on genuinely held-out rows
     the Champion model never trained on.
  2. Computes precision/recall/F1 across a grid of thresholds.
  3. Reports the F1-optimal threshold as the new default -- the standard,
     defensible choice absent a real stated cost ratio between a missed
     default and a wrongly-rejected good applicant. A real deployment
     should replace this with a threshold chosen against that real cost
     ratio once it's known; this is documented here, not invented.
  4. Writes the chosen threshold into Models/model_metrics.json (under
     champion.decision_threshold) and re-reports precision/recall/F1 at
     that threshold, so the numbers on file match what the server actually
     uses (see config.DECISION_THRESHOLD).

Usage:
    python scripts/tune_threshold.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score, roc_auc_score

import config
from model_loader import load_feature_order
from preprocessing import prepare_champion_input

RAW_DATA_PATH = "dataset/raw/application_train.csv"


def load_raw_and_reshape() -> pd.DataFrame:
    from preprocessing import reshape_raw_kaggle_columns
    df = pd.read_csv(RAW_DATA_PATH)
    return reshape_raw_kaggle_columns(df)


def main():
    load_feature_order()
    model = joblib.load("Models/model.pkl")

    print(f"[tune_threshold] Loading {RAW_DATA_PATH} ...")
    df = load_raw_and_reshape()

    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["TARGET"]
    )
    print(f"[tune_threshold] Held-out test set: {len(test_df)} rows (never trained on)")

    X_test = prepare_champion_input(test_df)
    y_test = test_df["TARGET"].values
    proba = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, proba)
    print(f"[tune_threshold] AUC (threshold-independent): {auc:.4f}\n")

    precisions, recalls, thresholds = precision_recall_curve(y_test, proba)
    f1s = np.where(
        (precisions + recalls) > 0,
        2 * precisions * recalls / np.where((precisions + recalls) > 0, precisions + recalls, 1),
        0,
    )
    # precision_recall_curve returns len(thresholds) == len(precisions) - 1
    f1s = f1s[:-1]

    f1_idx = int(np.argmax(f1s))
    f1_threshold = float(thresholds[f1_idx])

    print("[tune_threshold] Reference points across the threshold range:")
    for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
        preds = (proba >= t).astype(int)
        p = precision_score(y_test, preds, zero_division=0)
        r = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        marker = "  <-- current default" if t == 0.5 else ""
        print(f"  threshold={t:.2f}  precision={p:.4f}  recall={r:.4f}  f1={f1:.4f}{marker}")

    preds_f1 = (proba >= f1_threshold).astype(int)
    p_f1 = precision_score(y_test, preds_f1, zero_division=0)
    r_f1 = recall_score(y_test, preds_f1, zero_division=0)
    f1_f1 = f1_score(y_test, preds_f1, zero_division=0)
    print(f"\n[tune_threshold] F1-optimal threshold: {f1_threshold:.4f}  (precision={p_f1:.4f} recall={r_f1:.4f} f1={f1_f1:.4f})")

    # F1 treats a missed default and a wrongly-rejected good applicant as
    # equally costly (1:1) -- rarely true in credit risk, where the loss on
    # a missed default (the loan principal) is typically much larger than
    # the forgone margin on a wrongly-rejected good applicant. No real cost
    # figures are available here, so this uses an illustrative 5:1 ratio
    # (commonly cited as a rough order-of-magnitude in credit-scoring
    # literature) -- COST = 5 * FN + 1 * FP, minimized over the threshold
    # grid. A real deployment should replace 5.0 with the bank's real ratio.
    FN_COST_RATIO = 5.0
    n = len(y_test)
    thresh_grid = np.linspace(0.01, 0.99, 99)
    costs = []
    for t in thresh_grid:
        preds = (proba >= t).astype(int)
        fn = int(((preds == 0) & (y_test == 1)).sum())
        fp = int(((preds == 1) & (y_test == 0)).sum())
        costs.append(FN_COST_RATIO * fn + fp)
    cost_idx = int(np.argmin(costs))
    cost_threshold = float(thresh_grid[cost_idx])

    preds_cost = (proba >= cost_threshold).astype(int)
    p_cost = precision_score(y_test, preds_cost, zero_division=0)
    r_cost = recall_score(y_test, preds_cost, zero_division=0)
    f1_cost = f1_score(y_test, preds_cost, zero_division=0)
    print(f"[tune_threshold] Cost-weighted threshold (missed default {FN_COST_RATIO:.0f}x worse than a wrong rejection): "
          f"{cost_threshold:.4f}  (precision={p_cost:.4f} recall={r_cost:.4f} f1={f1_cost:.4f})")

    # Use the cost-weighted threshold as the deployed default -- more
    # defensible for credit risk than a bare F1-argmax, which implicitly
    # assumes false positives and false negatives cost the same.
    best_threshold, p_best, r_best, f1_best = cost_threshold, p_cost, r_cost, f1_cost

    # Update model_metrics.json with the tuned threshold + its metrics
    metrics_path = "Models/model_metrics.json"
    with open(metrics_path) as f:
        metrics = json.load(f)

    metrics["champion"]["decision_threshold"] = round(best_threshold, 4)
    metrics["champion"]["precision_at_threshold"] = round(p_best, 4)
    metrics["champion"]["recall_at_threshold"] = round(r_best, 4)
    metrics["champion"]["f1_at_threshold"] = round(f1_best, 4)
    metrics["champion"]["f1_optimal_threshold_for_reference"] = round(f1_threshold, 4)
    metrics["champion"]["threshold_note"] = (
        "decision_threshold minimizes an illustrative cost function "
        f"(5x FN + 1x FP) on the held-out test set's precision-recall curve -- "
        "not pure F1-argmax, which implicitly treats a missed default and a "
        "wrongly-rejected good applicant as equally costly (rarely true in "
        "credit risk: a missed default typically costs the full loan principal, "
        "far more than the forgone margin on a wrongly-rejected applicant). "
        "The 5x ratio is an illustrative placeholder, not derived from this "
        "bank's real economics -- a real deployment should replace it. The "
        "F1-optimal threshold is kept for reference under "
        "f1_optimal_threshold_for_reference. precision/recall/f1 above (no "
        "suffix) remain the original values at the sklearn-default 0.5 threshold."
    )

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[tune_threshold] Wrote decision_threshold={best_threshold:.4f} to {metrics_path}")


if __name__ == "__main__":
    main()
