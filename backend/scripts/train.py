"""
Champion + Challenger Training — The Drifting Oracle
=======================================================

Real training, on real labeled data (Kaggle Home Credit Default Risk,
application_train.csv, 307,511 rows, TARGET column). Replaces the two
static, undocumented .pkl files that shipped with zero lineage.

What this does:
  1. Loads application_train.csv, reshapes raw Kaggle columns into the
     schema preprocessing.py already expects (same functions the live
     server uses -- no separate/duplicated feature logic).
  2. Champion: trains LogisticRegression (baseline) + XGBoost on the
     20-feature schema, logs both to MLflow, evaluates with
     mlflow.evaluate(), keeps the better one.
  3. Challenger: trains XGBoost on the 8-feature schema (via
     engineer_challenger_features -- the same mapping the server uses
     to score Home-Credit-shaped batches against the "German" model),
     logs + evaluates the same way.
  4. Registers both winners in the Unity Catalog Model Registry with
     @champion / @challenger aliases.
  5. Overwrites the local Models/*.pkl the live server loads (after
     backing up the previous ones), so the running app benefits
     immediately -- and logs the promotion decision as a governance
     event in Delta.

Usage:
    python scripts/train.py
"""
import os
import sys
import shutil
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Force the non-interactive backend BEFORE matplotlib is imported by anything
# (mlflow.evaluate() pulls it in internally to render confusion-matrix/ROC/PR
# plots). Without this, matplotlib can pick an interactive backend that hangs
# indefinitely waiting for a display that doesn't exist in a background process.
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib
matplotlib.use("Agg")

import joblib
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier
from dotenv import load_dotenv

load_dotenv()

import config
from model_loader import load_feature_order
from preprocessing import prepare_champion_input, engineer_challenger_features

RAW_DATA_PATH = "dataset/raw/application_train.csv"
CATALOG = os.getenv("DATABRICKS_CATALOG", "drifting_oracle")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "monitoring")
USER_EMAIL = "solankirudra66@gmail.com"
EXPERIMENT_PATH = f"/Users/{USER_EMAIL}/drifting-oracle"

CHAMPION_UC_NAME = f"{CATALOG}.{SCHEMA}.champion_credit_model"
CHALLENGER_UC_NAME = f"{CATALOG}.{SCHEMA}.challenger_credit_model"


def load_raw_and_reshape() -> pd.DataFrame:
    """Load Kaggle's raw application_train.csv and reshape it into the
    column schema preprocessing.py's functions expect."""
    print(f"[train] Loading {RAW_DATA_PATH} ...")
    df = pd.read_csv(RAW_DATA_PATH)
    print(f"[train]   {len(df)} rows, {len(df.columns)} raw columns")

    df = df.rename(columns={"AMT_CREDIT": "AMT_CREDIT_x"})
    df["CODE_GENDER_M"] = (df["CODE_GENDER"] == "M").astype(int)
    df["CODE_GENDER_XNA"] = (df["CODE_GENDER"] == "XNA").astype(int)
    df["FLAG_OWN_CAR_Y"] = (df["FLAG_OWN_CAR"] == "Y").astype(int)
    df["FLAG_OWN_REALTY_Y"] = (df["FLAG_OWN_REALTY"] == "Y").astype(int)

    return df


def evaluate_model(model, X_test, y_test, threshold: float = 0.5) -> dict:
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= threshold).astype(int)
    return {
        "auc": round(roc_auc_score(y_test, proba), 4),
        "precision": round(precision_score(y_test, preds, zero_division=0), 4),
        "recall": round(recall_score(y_test, preds, zero_division=0), 4),
        "f1": round(f1_score(y_test, preds, zero_division=0), 4),
    }


def log_and_evaluate(run_name: str, model, X_test, y_test, params: dict, flavor) -> tuple:
    """Log a trained model to MLflow and log real evaluation metrics.

    NOTE: mlflow.evaluate() (the built-in classifier evaluator) was tried here and
    reproducibly hung with 0% CPU usage across multiple attempts in this environment
    -- once past a SHAP explainability bottleneck, then again inside the evaluator
    itself, even with matplotlib forced to a non-interactive backend. It's also
    flagged deprecated by MLflow 3.0 in favor of mlflow.models.evaluate(). Rather than
    depend on a flaky, deprecated call, metrics are computed directly with sklearn
    (evaluate_model, below) on the full held-out test set and logged straight to
    MLflow -- same numbers, no network-dependent black box in the training loop.
    """
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)
        model_info = flavor.log_model(model, name="model", input_example=X_test.head(3))

        metrics = evaluate_model(model, X_test, y_test)
        mlflow.log_metrics(metrics)
        print(f"[train]   {run_name}: {metrics}")
        return metrics, model_info.model_uri, run.info.run_id


def register_and_alias(model_uri: str, uc_name: str, alias: str) -> str:
    result = mlflow.register_model(model_uri=model_uri, name=uc_name)
    client = mlflow.MlflowClient()
    client.set_registered_model_alias(name=uc_name, alias=alias, version=result.version)
    print(f"[train]   Registered {uc_name} v{result.version} -> @{alias}")
    return result.version


def backup_and_save(model, local_path: str):
    if os.path.exists(local_path):
        backup_path = local_path + f".bak-{int(time.time())}"
        shutil.copy2(local_path, backup_path)
        print(f"[train]   Backed up existing model to {backup_path}")
    joblib.dump(model, local_path)
    print(f"[train]   Wrote {local_path}")


def main():
    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(EXPERIMENT_PATH)

    load_feature_order()  # populates config.FEATURE_ORDER from features.txt

    df = load_raw_and_reshape()
    y = df["TARGET"]

    train_df, test_df, y_train, y_test = train_test_split(
        df, y, test_size=0.2, random_state=42, stratify=y
    )
    # prepare_champion_input/engineer_challenger_features build their output via
    # .values (positional), which drops the original scattered row index and
    # replaces it with a fresh 0..N-1 range. Reset y_train/y_test the same way so
    # index-based lookups (e.g. eval_df sampling) stay correctly aligned with X.
    y_train = y_train.reset_index(drop=True)
    y_test = y_test.reset_index(drop=True)

    # ------------------------------------------------------------
    # CHAMPION -- 20-feature Home Credit schema
    # ------------------------------------------------------------
    print("\n=== Champion (Home Credit, 20 features) ===")
    X_train = prepare_champion_input(train_df)
    X_test = prepare_champion_input(test_df)

    logreg = LogisticRegression(max_iter=1000, class_weight="balanced")
    logreg.fit(X_train, y_train)
    logreg_metrics, logreg_uri, _ = log_and_evaluate(
        "champion-logreg", logreg, X_test, y_test,
        {"model_type": "LogisticRegression", "class_weight": "balanced"},
        mlflow.sklearn,
    )

    pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    xgb_champion = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        scale_pos_weight=pos_weight, eval_metric="auc", random_state=42,
    )
    xgb_champion.fit(X_train, y_train)
    xgb_metrics, xgb_uri, _ = log_and_evaluate(
        "champion-xgboost", xgb_champion, X_test, y_test,
        {"model_type": "XGBClassifier", "n_estimators": 200, "max_depth": 5,
         "learning_rate": 0.05, "scale_pos_weight": round(pos_weight, 2)},
        mlflow.xgboost,
    )

    if xgb_metrics["auc"] >= logreg_metrics["auc"]:
        champion_model, champion_uri, champion_metrics = xgb_champion, xgb_uri, xgb_metrics
        print(f"[train] Champion winner: XGBoost (AUC {xgb_metrics['auc']} vs LogReg {logreg_metrics['auc']})")
    else:
        champion_model, champion_uri, champion_metrics = logreg, logreg_uri, logreg_metrics
        print(f"[train] Champion winner: LogisticRegression (AUC {logreg_metrics['auc']} vs XGB {xgb_metrics['auc']})")

    champion_version = register_and_alias(champion_uri, CHAMPION_UC_NAME, "champion")
    backup_and_save(champion_model, "Models/model.pkl")

    # ------------------------------------------------------------
    # CHALLENGER -- 8-feature "German" schema, same underlying data
    # ------------------------------------------------------------
    print("\n=== Challenger (8-feature schema, same data) ===")
    Xc_train = engineer_challenger_features(train_df)
    Xc_test = engineer_challenger_features(test_df)

    pos_weight_c = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    xgb_challenger = XGBClassifier(
        n_estimators=150, max_depth=4, learning_rate=0.08,
        scale_pos_weight=pos_weight_c, eval_metric="auc", random_state=42,
    )
    xgb_challenger.fit(Xc_train, y_train)
    challenger_metrics, challenger_uri, _ = log_and_evaluate(
        "challenger-xgboost", xgb_challenger, Xc_test, y_test,
        {"model_type": "XGBClassifier", "n_estimators": 150, "max_depth": 4,
         "learning_rate": 0.08, "scale_pos_weight": round(pos_weight_c, 2), "schema": "8-feature"},
        mlflow.xgboost,
    )

    challenger_version = register_and_alias(challenger_uri, CHALLENGER_UC_NAME, "challenger")
    backup_and_save(xgb_challenger, "Models/model_german.pkl")

    # ------------------------------------------------------------
    # Log the promotion decision as a governance event (Delta)
    # ------------------------------------------------------------
    import databricks_io
    databricks_io.insert_governance_event(
        "MODEL_TRAINED",
        (
            f"Champion v{champion_version} ({type(champion_model).__name__}, "
            f"AUC={champion_metrics['auc']}, precision={champion_metrics['precision']}, "
            f"recall={champion_metrics['recall']}) trained on {len(train_df)} rows of "
            f"application_train.csv. Challenger v{challenger_version} (XGBoost, "
            f"AUC={challenger_metrics['auc']}) trained on the same data via the 8-feature "
            f"schema. Both registered in Unity Catalog with @champion/@challenger aliases."
        ),
        "training-pipeline",
    )

    print("\n=== Summary ===")
    print(f"Champion  ({type(champion_model).__name__}): {champion_metrics}  -> {CHAMPION_UC_NAME}@champion v{champion_version}")
    print(f"Challenger (XGBoost):              {challenger_metrics}  -> {CHALLENGER_UC_NAME}@challenger v{challenger_version}")


if __name__ == "__main__":
    main()
