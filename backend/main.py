"""
The Drifting Oracle -- FastAPI Application
==========================================

Drift-aware credit default prediction system.

Pipeline (for /predict_batch):
  1. Parse uploaded CSV
  2. Multi-feature PSI comparison: incoming data vs training baseline
  3. Model selection: PSI < 0.25 -> Champion, PSI >= 0.25 -> Challenger
  4. Feature engineering (server-side, NOT from user input)
  5. predict_proba -> probability scores
  6. Risk labeling: Low / Medium / High
  7. Structured JSON response with per-row predictions

Modules:
  - config.py          -> constants & shared state
  - model_loader.py    -> model/feature loading
  - preprocessing.py   -> feature engineering + ChampionChallenger mapping
  - psi.py             -> multi-feature PSI calculation
  - schemas.py         -> Pydantic request models
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any LLM imports
load_dotenv()

# Force UTF-8 output on Windows (prevents cp1252 UnicodeEncodeError in print)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import config
import databricks_io
import retrain
from model_loader import load_feature_order, load_model
from psi import build_baseline_distributions, calculate_multi_feature_psi
from preprocessing import (
    prepare_champion_input,
    prepare_challenger_input,
    engineer_champion_features,
    get_risk_label,
)
from schemas import PredictRequest
from llm_explanation import generate_explanation, generate_batch_explanation


# ----------------------------------------------
# Startup / Lifespan
# ----------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize all models, feature orders, and baseline distributions.
    Runs once when the server starts, before it accepts any requests.
    """
    # 1. Load feature order from features.txt
    load_feature_order()

    # 2. Load Champion + Challenger models
    load_model()

    # 3. Load baseline dataset and compute PSI reference distributions
    for path in config.BASELINE_PATHS:
        if os.path.exists(path):
            try:
                config.BASELINE_DATA = pd.read_csv(path)

                # Engineer features on baseline so PSI features like
                # income_credit_ratio are available for comparison
                config.BASELINE_DATA = engineer_champion_features(config.BASELINE_DATA)

                # Build per-feature bin edges and distributions
                build_baseline_distributions(config.BASELINE_DATA)

                print(f"[startup] Baseline loaded from {path} ({len(config.BASELINE_DATA)} rows)")
                config.log_governance_event(
                    "SYSTEM_STARTUP",
                    f"Baseline loaded from {path} ({len(config.BASELINE_DATA)} rows, "
                    f"{len(config.BASELINE_DISTRIBUTIONS)} PSI features)",
                    "system",
                )
            except Exception as e:
                print(f"[startup] Error processing baseline: {e}")
                config.BASELINE_DATA = None
            break
    else:
        print("[startup] Warning: No baseline file found.")

    # Log model status
    if config.MODEL is not None:
        config.log_governance_event(
            "MODEL_LOADED",
            f"Champion model loaded ({len(config.FEATURE_ORDER)} features, {type(config.MODEL).__name__})",
            "champion",
        )
    if config.GERMAN_MODEL is not None:
        config.log_governance_event(
            "MODEL_LOADED",
            f"Challenger model loaded ({getattr(config.GERMAN_MODEL, 'n_features_in_', '?')} features, "
            f"{type(config.GERMAN_MODEL).__name__})",
            "challenger",
        )

    yield  # server runs here -- nothing needed on shutdown


# ----------------------------------------------
# App Init
# ----------------------------------------------
app = FastAPI(title="The Drifting Oracle API", lifespan=lifespan)

FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------
# Core Prediction Pipeline
# ----------------------------------------------

def select_model(drift_detected: bool) -> tuple:
    """
    Model selection logic based on PSI drift status.
    
    IF PSI < 0.25 -> Champion model (stable distribution)
    ELSE          -> Challenger model (distribution has drifted)
    
    Returns (model_object, model_name_string)
    """
    if drift_detected and config.GERMAN_MODEL is not None:
        return config.GERMAN_MODEL, "Challenger"
    else:
        return config.MODEL, "Champion"


def run_predictions(model, input_df: pd.DataFrame) -> list[dict]:
    """
    Run predict_proba on the input DataFrame and return per-row results.
    
    Uses predict_proba to get probability of default (class 1),
    then maps to risk labels: Low / Medium / High.
    
    Returns list of:
      {"id": int, "probability": float, "risk_label": str}
    """
    # predict_proba returns [[P(class=0), P(class=1)], ...]
    probabilities = model.predict_proba(input_df)

    # Extract probability of default (class 1)
    default_probs = probabilities[:, 1]

    predictions = []
    for i, prob in enumerate(default_probs):
        prob_rounded = round(float(prob), 4)
        predictions.append({
            "id": i,
            "probability": prob_rounded,
            "risk_label": get_risk_label(prob_rounded),
        })

    return predictions


# ----------------------------------------------
# Endpoints
# ----------------------------------------------

@app.get("/")
async def root():
    return {"message": "Welcome to The Drifting Oracle"}


@app.get("/api/health")
async def health():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": config.MODEL is not None,
        "challenger_loaded": config.GERMAN_MODEL is not None,
        "features_count": len(config.FEATURE_ORDER),
        "baseline_loaded": config.BASELINE_DATA is not None,
        "psi_features": list(config.BASELINE_DISTRIBUTIONS.keys()),
    }


@app.post("/predict")
async def predict(data: PredictRequest):
    """
    Single-row prediction via JSON input.
    Returns probability + risk label + PSI status.
    """
    if config.MODEL is None:
        return {"status": "failed", "error": "Model not loaded"}

    input_dict = data.model_dump()

    # Create a single-row DataFrame
    input_df = pd.DataFrame([input_dict])

    # Compute PSI against baseline
    input_df_engineered = engineer_champion_features(input_df)
    overall_psi, psi_per_feature, drift_detected = calculate_multi_feature_psi(input_df_engineered)

    # Select model
    model, model_used = select_model(drift_detected)

    # Prepare features for the selected model
    try:
        if model_used == "Champion":
            model_input = prepare_champion_input(input_df)
        else:
            model_input = prepare_challenger_input(input_df)
    except Exception as e:
        return {"status": "failed", "error": f"Feature preparation failed: {str(e)}"}

    # Predict
    try:
        predictions = run_predictions(model, model_input)
    except Exception as e:
        return {"status": "failed", "error": f"Prediction failed: {str(e)}"}

    pred = predictions[0]

    # Generate LLM explanation
    psi_status = "drift_detected" if drift_detected else "no_drift"
    llm_result = generate_explanation(pred["probability"], overall_psi, psi_status)
    
    print(f"[predict] LLM Used: {llm_result['llm_used']}")

    # Track
    config.PREDICTION_COUNT += 1
    if drift_detected:
        config.DRIFT_COUNT += 1
    
    # Log LLM evaluation for monitoring
    eval_record = config.log_llm_evaluation(llm_result["explanation"], llm_result["llm_used"], pred["probability"])

    decision = "Reject Loan" if pred["probability"] >= 0.5 else "Accept Loan"
    databricks_io.insert_prediction(
        total_rows=1,
        avg_probability=pred["probability"],
        default_rate=1.0 if pred["probability"] >= 0.5 else 0.0,
        model_used=model_used,
        overall_psi=overall_psi,
        drift_detected=drift_detected,
        decision=decision,
    )

    return {
        "status": "success",
        "psi": overall_psi,
        "psi_per_feature": psi_per_feature,
        "drift_detected": drift_detected,
        "model_used": model_used,
        "probability": pred["probability"],
        "risk_label": pred["risk_label"],
        "decision": decision,
        "explanation": llm_result["explanation"],
        "explanation_llm": llm_result["llm_used"],
        "llm_evaluation": eval_record["evaluation"]
    }


@app.post("/predict_batch")
async def predict_batch(file: UploadFile = File(...)):
    """
    Batch prediction endpoint -- the core pipeline.
    
    Pipeline:
      1. Parse CSV file
      2. Compute multi-feature PSI (incoming vs training baseline)
      3. Select model based on PSI threshold (0.25)
      4. Engineer features server-side
      5. Run predict_proba for all rows
      6. Return structured JSON with per-row predictions
    
    Returns:
      {
        "status": "success",
        "psi": float,
        "psi_per_feature": {feature: score, ...},
        "drift_detected": bool,
        "model_used": "Champion" | "Challenger",
        "total_rows": int,
        "predictions": [{"id": int, "probability": float, "risk_label": str}, ...]
      }
    """
    # -- Guard: file type ------------------------
    if not file.filename.endswith(".csv"):
        return {"status": "failed", "error": "Only .csv files are supported."}

    if config.MODEL is None:
        return {"status": "failed", "error": "Champion model not loaded."}

    # -- Step 1: Parse CSV ----------------------
    try:
        df = pd.read_csv(file.file)
    except pd.errors.EmptyDataError:
        # A genuinely empty file raises here -- pandas never gets far enough
        # to hand back a DataFrame for the df.empty check below to catch.
        return {"status": "failed", "error": "CSV file is empty."}
    except Exception as e:
        return {"status": "failed", "error": f"Invalid CSV file: {str(e)}"}

    if df.empty:
        return {"status": "failed", "error": "CSV file is empty."}

    print(f"\n[predict_batch] Received CSV: {len(df)} rows, {len(df.columns)} columns")
    print(f"[predict_batch] Columns: {list(df.columns)}")

    # -- Step 2: Feature Engineering (for PSI) --
    # Engineer features so PSI can compare income_credit_ratio etc.
    df_engineered = engineer_champion_features(df)

    # -- Step 3: Multi-Feature PSI --------------
    # Compare incoming data distribution vs training baseline
    # across >=5 key numeric features
    if config.BASELINE_DATA is not None and config.BASELINE_DISTRIBUTIONS:
        overall_psi, psi_per_feature, drift_detected = calculate_multi_feature_psi(df_engineered)
    else:
        # No baseline -> assume no drift
        print("[predict_batch] Warning: No baseline loaded, skipping PSI.")
        overall_psi = 0.0
        psi_per_feature = {}
        drift_detected = False

    # -- Step 4: Model Selection ----------------
    # PSI < 0.25 -> Champion | PSI >= 0.25 -> Challenger
    model, model_used = select_model(drift_detected)
    print(f"[predict_batch] PSI = {overall_psi} -> Model: {model_used}")

    # -- Step 5: Prepare Features ----------------
    # Engineer features server-side for the selected model
    try:
        if model_used == "Champion":
            model_input = prepare_champion_input(df)
        else:
            model_input = prepare_challenger_input(df)
    except Exception as e:
        return {"status": "failed", "error": f"Feature preparation failed: {str(e)}"}

    # -- Step 6: Predictions (predict_proba) ----
    try:
        predictions = run_predictions(model, model_input)
    except Exception as e:
        return {"status": "failed", "error": f"Prediction failed: {str(e)}"}

    # -- Step 7: Tracking & Governance ----------
    config.PREDICTION_COUNT += len(df)

    if drift_detected:
        config.DRIFT_COUNT += 1

    config.log_drift_detection(overall_psi, psi_per_feature, drift_detected)
    config.log_governance_event(
        "BATCH_PREDICTION",
        f"Batch of {len(df)} rows. PSI={overall_psi}, model={model_used}, "
        f"drift={'YES' if drift_detected else 'NO'}",
        model_used,
    )

    if drift_detected:
        config.log_governance_event(
            "DRIFT_ALERT",
            f"Distribution shift detected -- PSI={overall_psi} (threshold={config.PSI_THRESHOLD}). "
            f"Switched to {model_used} model.",
            model_used,
        )
        retrain.maybe_trigger_retrain()

    # -- Step 8: Compute Summary Statistics (before LLM explanation) ----
    probabilities = [p["probability"] for p in predictions]
    avg_probability = round(sum(probabilities) / len(probabilities), 4) if probabilities else 0.0
    default_rate = round(sum(1 for p in probabilities if p >= 0.5) / len(probabilities), 4) if probabilities else 0.0

    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for p in predictions:
        risk_counts[p["risk_label"]] += 1

    # -- Step 9: Generate LLM Explanation -------
    psi_status = "drift_detected" if drift_detected else "no_drift"
    llm_result = generate_batch_explanation(default_rate, overall_psi, psi_status)
    
    print(f"[predict_batch] LLM Used: {llm_result['llm_used']}")

    # -- Step 10: Log LLM Evaluation -------
    eval_record = config.log_llm_evaluation(llm_result["explanation"], llm_result["llm_used"], default_rate)

    # -- Step 10b: Log Prediction Batch (Delta) ----
    batch_decision = "Reject Loan" if default_rate >= 0.5 else "Accept Loan"
    databricks_io.insert_prediction(
        total_rows=len(df),
        avg_probability=avg_probability,
        default_rate=default_rate,
        model_used=model_used,
        overall_psi=overall_psi,
        drift_detected=drift_detected,
        decision=batch_decision,
    )

    # -- Step 11: Build Response ------------------
    return {
        "status": "success",
        "psi": overall_psi,
        "psi_per_feature": psi_per_feature,
        "drift_detected": drift_detected,
        "model_used": model_used,
        "total_rows": len(df),
        "default_rate": default_rate,
        "avg_probability": avg_probability,
        "risk_distribution": risk_counts,
        "decision": batch_decision,
        "message": (
            f"Drift detected (PSI={overall_psi}). Switched to {model_used} model."
            if drift_detected
            else "System operating normally. No distribution shift detected."
        ),
        "explanation": llm_result["explanation"],
        "explanation_llm": llm_result["llm_used"],
        "llm_evaluation": eval_record["evaluation"],
        "predictions": predictions,
    }


# ----------------------------------------------
# Standalone PSI Endpoint
# ----------------------------------------------

@app.get("/psi")
async def get_psi():
    """Return current PSI configuration status."""
    return {
        "psi_features": config.PSI_FEATURES,
        "active_features": list(config.BASELINE_DISTRIBUTIONS.keys()),
        "threshold": config.PSI_THRESHOLD,
        "baseline_loaded": config.BASELINE_DATA is not None,
        "baseline_rows": len(config.BASELINE_DATA) if config.BASELINE_DATA is not None else 0,
    }


# ----------------------------------------------
# Simulation Helpers
# ----------------------------------------------

@app.post("/fill_window")
async def fill_window(count: int = 50, drift: bool = False):
    """
    Simulate a batch prediction by sampling from baseline.
    Use ?drift=true to inject drifted data for demo.
    
    This creates a synthetic CSV from baseline rows (optionally with
    artificial distribution shift) and runs it through the full pipeline.
    """
    import random

    if config.BASELINE_DATA is None:
        return {"status": "failed", "error": "Baseline data not loaded."}

    # Sample rows from baseline
    sample_df = config.BASELINE_DATA.sample(n=min(count, len(config.BASELINE_DATA)), replace=True).reset_index(drop=True)

    if drift:
        # Inject artificial drift by scaling numeric columns
        for col in ["AMT_CREDIT_x", "AMT_INCOME_TOTAL", "AMT_ANNUITY"]:
            if col in sample_df.columns:
                sample_df[col] = sample_df[col] * random.uniform(1.5, 2.5)
        for col in ["EXT_SOURCE_2", "EXT_SOURCE_3"]:
            if col in sample_df.columns:
                sample_df[col] = sample_df[col] * random.uniform(0.3, 0.6)

    # Engineer features for PSI
    sample_engineered = engineer_champion_features(sample_df)

    # Compute PSI
    overall_psi, psi_per_feature, drift_detected = calculate_multi_feature_psi(sample_engineered)

    # Track
    config.log_drift_detection(overall_psi, psi_per_feature, drift_detected)
    config.log_governance_event(
        "SIMULATION",
        f"Simulated {count} samples (drift={drift}). PSI={overall_psi}",
        "system",
    )
    if drift_detected:
        config.DRIFT_COUNT += 1

    return {
        "status": "success",
        "message": f"Simulated {count} samples" + (" (DRIFT MODE)" if drift else ""),
        "samples": count,
        "psi": overall_psi,
        "psi_per_feature": psi_per_feature,
        "drift_detected": drift_detected,
    }


# ----------------------------------------------
# Frontend API Endpoints
# ----------------------------------------------

@app.get("/api/v1/dashboard-metrics")
async def dashboard_metrics():
    """Aggregate metrics for the dashboard KPI cards."""
    total_models = sum(1 for m in [config.MODEL, config.GERMAN_MODEL] if m is not None)
    total_predictions = config.PREDICTION_COUNT
    drift_detections = config.DRIFT_COUNT
    drift_rate = round((drift_detections / total_predictions * 100), 2) if total_predictions > 0 else 0.0

    total_llm_evals = len(config.LLM_EVALUATIONS)
    hallucinated_evals = sum(1 for e in config.LLM_EVALUATIONS if e.get("evaluation", {}).get("hallucination", False))
    grounded_evals = sum(1 for e in config.LLM_EVALUATIONS if e.get("evaluation", {}).get("grounded", False))

    hallucination_rate = round((hallucinated_evals / total_llm_evals * 100), 2) if total_llm_evals > 0 else 0.0
    acceptable_rate = round((grounded_evals / total_llm_evals * 100), 2) if total_llm_evals > 0 else 0.0

    return {
        "total_models": total_models,
        "drift_detections": drift_detections,
        "drift_rate": drift_rate,
        "total_llm_evaluations": total_llm_evals,
        "hallucination_rate": hallucination_rate,
        "acceptable_rate": acceptable_rate,
        "governance_events": len(config.GOVERNANCE_LOG),
    }


@app.get("/api/v1/drift-history")
async def drift_history():
    """Return the list of past drift detection results."""
    return config.DRIFT_HISTORY


@app.get("/api/v1/models")
async def get_models():
    """Return info about loaded models."""
    models = []
    if config.MODEL is not None:
        models.append({
            "model_id": "champion-home-credit",
            "version": "v1.0",
            "type": "champion",
            "status": "active",
            "training_date": "Pre-trained",
            "metrics": {"auc": None, "precision": None, "recall": None},
        })
    if config.GERMAN_MODEL is not None:
        models.append({
            "model_id": "challenger-german-credit",
            "version": "v1.0",
            "type": "challenger",
            "status": "standby",
            "training_date": "Pre-trained",
            "metrics": {"auc": None, "precision": None, "recall": None},
        })
    return models


@app.get("/api/v1/llm-evaluations")
async def get_llm_evaluations():
    """Return the list of LLM evaluation results."""
    return config.LLM_EVALUATIONS


@app.get("/api/v1/governance-log")
async def get_governance_log():
    """Return the governance event log."""
    return config.GOVERNANCE_LOG
