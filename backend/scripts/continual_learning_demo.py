"""
Continual-Learning Harness -- does retraining actually adapt to a changing
world, or does it just re-fit the same fixed dataset?
=============================================================================

Context: the live server's drift-triggered retrain (retrain.py) re-runs
scripts/train.py against the same fixed, static application_train.csv every
time -- which is operationally real (proven live, see the interview PDF) but
does NOT demonstrate the model actually learning from new information, since
there IS no new information: Kaggle's Home Credit dataset is a single frozen
snapshot with no real per-row timestamps to build a genuine time-series
retraining loop from.

This script builds an honest, inspectable stand-in for that missing
timeline: it partitions the real dataset into non-overlapping "eras" and
applies a documented, progressive synthetic shift to simulate a population
that changes over a few years (incomes/credit amounts drift up, external
credit-bureau scores drift down -- the same style of shift already used
elsewhere in this project's /fill_window demo endpoint, just applied
deterministically and progressively instead of randomly). TARGET labels
carry over unchanged with each row -- this is a covariate-drift simulation
(the applicant population's feature distribution shifts), not a claim about
real economic history.

For each era transition, it:
  1. Computes PSI of the new era against the current baseline using the
     REAL production psi.py module -- not a reimplementation -- so a
     reported "drift detected" here is the same signal the live server
     would raise.
  2. Scores the new era with the CURRENT (pre-retrain) model -- "before".
  3. Retrains on a GROWING window (all eras seen so far, not just the
     newest one) using the same feature prep and XGBoost hyperparameters
     scripts/train.py uses, for a fair comparison.
  4. Scores the new era again with the retrained model -- "after".
  5. Also scores a held-out general evaluation pool with the retrained
     model, to confirm it isn't just overfitting to the newest era at the
     expense of everything else.

Everything (era datasets, trained model snapshots, the full report) is
written under continual_learning_demo/ -- entirely separate from Models/,
never touches the live server's actual deployed model.

Usage:
    python scripts/continual_learning_demo.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

import config
from model_loader import load_feature_order
from preprocessing import prepare_champion_input, reshape_raw_kaggle_columns, engineer_champion_features
from psi import build_baseline_distributions, calculate_multi_feature_psi

RAW_DATA_PATH = "dataset/raw/application_train.csv"
OUT_DIR = "continual_learning_demo"
N_ERAS = 4  # era 0 (baseline) + 3 simulated "future" eras
RANDOM_STATE = 42

# Progressive synthetic shift per era, relative to era 0 -- documented,
# deterministic, and the same style of transform /fill_window already uses
# elsewhere in this project to simulate drift for demo purposes.
ERA_SHIFTS = {
    # era_index: (amount_scale_multiplier, ext_source_shift)
    0: (1.00, 0.00),   # baseline -- unmodified
    1: (1.15, -0.05),  # mild drift
    2: (1.30, -0.10),  # moderate drift
    3: (1.50, -0.15),  # significant drift
}

AMOUNT_COLS = ["AMT_INCOME_TOTAL", "AMT_CREDIT_x", "AMT_ANNUITY"]
EXT_SOURCE_COLS = ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]


def apply_era_shift(df: pd.DataFrame, era: int) -> pd.DataFrame:
    df = df.copy()
    amt_scale, ext_shift = ERA_SHIFTS[era]
    for col in AMOUNT_COLS:
        if col in df.columns:
            df[col] = df[col] * amt_scale
    for col in EXT_SOURCE_COLS:
        if col in df.columns:
            df[col] = (df[col] + ext_shift).clip(lower=0.0, upper=1.0)
    return df


def train_xgb(X: pd.DataFrame, y: pd.Series) -> XGBClassifier:
    """Same hyperparameters and imbalance handling as scripts/train.py's
    Champion, so results are directly comparable."""
    scale_pos_weight = (y == 0).sum() / max((y == 1).sum(), 1)
    model = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        scale_pos_weight=scale_pos_weight, eval_metric="auc",
        random_state=RANDOM_STATE,
    )
    model.fit(X, y)
    return model


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    load_feature_order()

    print(f"[continual] Loading {RAW_DATA_PATH} ...")
    df = reshape_raw_kaggle_columns(pd.read_csv(RAW_DATA_PATH))
    print(f"[continual]   {len(df)} rows")

    # Held out ONCE, up front, stratified -- never used to build an era or
    # to train anything. The one honest "how well does this generalize"
    # check throughout the whole experiment.
    pool, eval_pool = train_test_split(
        df, test_size=0.15, random_state=RANDOM_STATE, stratify=df["TARGET"]
    )
    print(f"[continual] General eval pool (held out, never trained on): {len(eval_pool)} rows")

    # Non-overlapping era slices from the remaining pool.
    pool = pool.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)
    era_size = len(pool) // N_ERAS
    eras_raw = [pool.iloc[i * era_size:(i + 1) * era_size].copy() for i in range(N_ERAS)]
    for i, era_df in enumerate(eras_raw):
        print(f"[continual] Era {i} slice: {len(era_df)} rows (before synthetic shift)")

    eras = [apply_era_shift(era_df, i) for i, era_df in enumerate(eras_raw)]

    X_eval = prepare_champion_input(eval_pool)
    y_eval = eval_pool["TARGET"].values

    # --- Era 0: initial training (what the bank had "at launch") ---
    print("\n=== Era 0: initial training ===")
    X0 = prepare_champion_input(eras[0])
    y0 = eras[0]["TARGET"]
    model = train_xgb(X0, y0)
    auc_general_0 = roc_auc_score(y_eval, model.predict_proba(X_eval)[:, 1])
    print(f"[continual] Era-0 model AUC on general eval pool: {auc_general_0:.4f}")

    # PSI baseline = era 0's distribution, via the real production module.
    # engineer_champion_features() computes income_credit_ratio/age/etc --
    # the same step main.py runs before every real PSI check -- without it,
    # calculate_multi_feature_psi silently skips any engineered feature
    # missing from the raw columns rather than computing it.
    baseline_engineered = engineer_champion_features(eras[0])
    build_baseline_distributions(baseline_engineered)

    cumulative = [eras[0]]
    report = {
        "eval_pool_size": len(eval_pool),
        "era_size": era_size,
        "era_shifts": ERA_SHIFTS,
        "era0_model_auc_on_general_eval": round(float(auc_general_0), 4),
        "eras": [],
    }

    for era_idx in range(1, N_ERAS):
        print(f"\n=== Era {era_idx}: simulated drift + retrain ===")
        era_df = eras[era_idx]
        era_engineered = engineer_champion_features(era_df)

        # 1. Real PSI check via the actual production module.
        overall_psi, psi_per_feature, drift_detected = calculate_multi_feature_psi(era_engineered)
        print(f"[continual] PSI (era {era_idx} vs baseline) = {overall_psi:.4f}  drift_detected={drift_detected}")

        # 2. Score with the CURRENT (pre-retrain) model -- "before".
        X_era = prepare_champion_input(era_df)
        y_era = era_df["TARGET"].values
        auc_before = roc_auc_score(y_era, model.predict_proba(X_era)[:, 1])

        # 3. Retrain on the GROWING window: every era seen so far.
        cumulative.append(era_df)
        train_df = pd.concat(cumulative, ignore_index=True)
        X_train = prepare_champion_input(train_df)
        y_train = train_df["TARGET"]
        t0 = time.time()
        model = train_xgb(X_train, y_train)
        elapsed = round(time.time() - t0, 1)
        print(f"[continual] Retrained on {len(train_df)} cumulative rows in {elapsed}s")

        # 4. Score the SAME era again -- "after".
        auc_after = roc_auc_score(y_era, model.predict_proba(X_era)[:, 1])

        # 5. General-pool check -- did it get better at the new era without
        #    forgetting how to generalize?
        auc_general_after = roc_auc_score(y_eval, model.predict_proba(X_eval)[:, 1])

        print(f"[continual] AUC on era {era_idx}: before={auc_before:.4f} -> after={auc_after:.4f}  "
              f"(general eval pool: {auc_general_after:.4f})")

        model.save_model(os.path.join(OUT_DIR, f"model_after_era_{era_idx}.json"))

        report["eras"].append({
            "era": era_idx,
            "rows_in_era": len(era_df),
            "cumulative_training_rows": len(train_df),
            "psi_vs_baseline": round(float(overall_psi), 4),
            "drift_detected": bool(drift_detected),
            "psi_per_feature": {k: round(float(v), 4) for k, v in psi_per_feature.items()},
            "auc_before_retrain": round(float(auc_before), 4),
            "auc_after_retrain": round(float(auc_after), 4),
            "auc_delta": round(float(auc_after - auc_before), 4),
            "auc_general_eval_pool_after_retrain": round(float(auc_general_after), 4),
            "retrain_seconds": elapsed,
        })

    report_path = os.path.join(OUT_DIR, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Era':<5}{'PSI':<10}{'Drift?':<9}{'AUC before':<13}{'AUC after':<12}{'Delta':<9}{'General pool':<13}")
    for e in report["eras"]:
        print(f"{e['era']:<5}{e['psi_vs_baseline']:<10}{str(e['drift_detected']):<9}"
              f"{e['auc_before_retrain']:<13}{e['auc_after_retrain']:<12}"
              f"{e['auc_delta']:+.4f}  {e['auc_general_eval_pool_after_retrain']:<13}")
    print(f"\n[continual] Full report written to {report_path}")


if __name__ == "__main__":
    main()
