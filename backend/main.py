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
from fastapi.responses import JSONResponse

import config
import databricks_io
import retrain
from model_loader import load_feature_order, load_model
from psi import build_baseline_distributions, calculate_multi_feature_psi
from preprocessing import (
    prepare_champion_input,
    prepare_challenger_input,
    engineer_champion_features,
    reshape_raw_kaggle_columns,
    get_risk_label,
)
from schemas import PredictRequest
from llm_graph import run_explanation_graph


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

                # Raw Kaggle files (e.g. application_train.csv) still use
                # Kaggle's original column names/types -- reshape them into
                # the schema engineer_champion_features() expects. A no-op
                # on files that are already in that schema (AMT_CREDIT_x
                # etc. already present).
                config.BASELINE_DATA = reshape_raw_kaggle_columns(config.BASELINE_DATA)

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

# Routes reachable with no key even when API_KEY is set -- health checks
# need to work for K8s liveness/readiness probes and uptime monitors that
# were never going to carry a secret, and CORS preflight (OPTIONS) never
# carries app headers by design, so gating it would just break every
# cross-origin request before the browser ever sends the real one.
_AUTH_EXEMPT_PATHS = {"/", "/api/health"}


@app.middleware("http")
async def require_api_key(request, call_next):
    """Minimal shared-secret gate -- see config.API_KEY's docstring for why
    this is deliberately not a full user-auth system. A no-op (every
    request passes) whenever API_KEY is unset, so local dev/CI/tests need
    zero configuration; the moment an operator sets API_KEY, every route
    except the health-check exemptions above requires a matching
    X-API-Key header, closing the "anyone who can reach the API can hit
    every route" gap named in the project's known limitations.
    """
    if (
        config.API_KEY is not None
        and request.method != "OPTIONS"
        and request.url.path not in _AUTH_EXEMPT_PATHS
        and request.headers.get("x-api-key") != config.API_KEY
    ):
        return _error(401, "Missing or invalid X-API-Key header.")
    return await call_next(request)


# ----------------------------------------------
# Core Prediction Pipeline
# ----------------------------------------------

def _error(status_code: int, message: str) -> JSONResponse:
    """A failure response with a real HTTP status code attached.

    Every failure path used to `return {"status": "failed", "error": ...}`
    with FastAPI's default 200 -- any client that checks the HTTP status
    code rather than parsing the body would see every one of these as a
    success. Keeps the same body shape the frontend already checks
    (`result.status !== 'success'`), just with a correct status code.
    """
    return JSONResponse(status_code=status_code, content={"status": "failed", "error": message})


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
    Returns probability + risk label.

    PSI is a population-level statistic -- it is not computed here and does
    not select a model. A histogram of a single data point against 10
    quantile bins always puts 100% of the mass in one bin, which produces an
    extreme PSI (empirically ~12+) regardless of how typical the applicant
    is; verified live by feeding it an applicant set to the literal median
    of every baseline feature, which still scored PSI~12.5. Population drift
    is only meaningful, and only computed, on a batch (see /predict_batch).
    Single-row prediction always uses the Champion model.
    """
    if config.MODEL is None:
        return _error(503, "Model not loaded")

    input_dict = data.model_dump()

    # Create a single-row DataFrame
    input_df = pd.DataFrame([input_dict])

    model, model_used = config.MODEL, "Champion"

    # Prepare features for the selected model
    try:
        model_input = prepare_champion_input(input_df)
    except Exception as e:
        return _error(400, f"Feature preparation failed: {str(e)}")
    missing_features = model_input.attrs.get("missing_features", [])

    # Predict
    try:
        predictions = run_predictions(model, model_input)
    except Exception as e:
        return _error(400, f"Prediction failed: {str(e)}")

    pred = predictions[0]

    # Generate LLM explanation via the predict->explain->evaluate graph
    # (retries once, with feedback, if the grounding check flags a
    # hallucination on the first attempt -- see llm_graph.py). Single-row
    # predict has no population-level drift signal (see docstring above),
    # so the graph is always given "no_drift".
    graph_result = run_explanation_graph("single", pred["probability"], 0.0, "no_drift")
    llm_result = {"explanation": graph_result["explanation"], "llm_used": graph_result["llm_used"]}

    print(f"[predict] LLM Used: {llm_result['llm_used']} (attempts={graph_result['attempts']}, retried={graph_result['retried']})")

    # Track
    config.PREDICTION_COUNT += 1

    # Log LLM evaluation for monitoring (eval already computed by the graph)
    eval_record = config.log_llm_evaluation(
        llm_result["explanation"], llm_result["llm_used"], pred["probability"], eval_result=graph_result["eval_result"]
    )

    decision = "Reject Loan" if pred["probability"] >= config.get_decision_threshold() else "Accept Loan"
    databricks_io.insert_prediction(
        total_rows=1,
        avg_probability=pred["probability"],
        default_rate=1.0 if pred["probability"] >= config.get_decision_threshold() else 0.0,
        model_used=model_used,
        overall_psi=None,
        drift_detected=False,
        decision=decision,
    )

    return {
        "status": "success",
        "model_used": model_used,
        "probability": pred["probability"],
        "risk_label": pred["risk_label"],
        "decision": decision,
        "explanation": llm_result["explanation"],
        "explanation_llm": llm_result["llm_used"],
        "llm_evaluation": eval_record["evaluation"],
        "warnings": (
            [f"Column(s) not found in input, defaulted to 0: {', '.join(missing_features)}"]
            if missing_features else []
        ),
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
        return _error(400, "Only .csv files are supported.")

    if config.MODEL is None:
        return _error(503, "Champion model not loaded.")

    # -- Step 1: Parse CSV ----------------------
    try:
        df = pd.read_csv(file.file)
    except pd.errors.EmptyDataError:
        # A genuinely empty file raises here -- pandas never gets far enough
        # to hand back a DataFrame for the df.empty check below to catch.
        return _error(400, "CSV file is empty.")
    except Exception as e:
        return _error(400, f"Invalid CSV file: {str(e)}")

    if df.empty:
        return _error(400, "CSV file is empty.")

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
        missing_features = model_input.attrs.get("missing_features", [])
    except Exception as e:
        return _error(400, f"Feature preparation failed: {str(e)}")

    # -- Step 6: Predictions (predict_proba) ----
    try:
        predictions = run_predictions(model, model_input)
    except Exception as e:
        return _error(400, f"Prediction failed: {str(e)}")

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
        retrain.maybe_trigger_retrain(df)

    # -- Step 8: Compute Summary Statistics (before LLM explanation) ----
    probabilities = [p["probability"] for p in predictions]
    avg_probability = round(sum(probabilities) / len(probabilities), 4) if probabilities else 0.0
    default_rate = round(sum(1 for p in probabilities if p >= config.get_decision_threshold()) / len(probabilities), 4) if probabilities else 0.0

    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    for p in predictions:
        risk_counts[p["risk_label"]] += 1

    # -- Step 9: Generate LLM Explanation via the predict->explain->evaluate
    #    graph (retries once, with feedback, on a flagged hallucination) --
    psi_status = "drift_detected" if drift_detected else "no_drift"
    graph_result = run_explanation_graph("batch", default_rate, overall_psi, psi_status)
    llm_result = {"explanation": graph_result["explanation"], "llm_used": graph_result["llm_used"]}

    print(f"[predict_batch] LLM Used: {llm_result['llm_used']} (attempts={graph_result['attempts']}, retried={graph_result['retried']})")

    # -- Step 10: Log LLM Evaluation (eval already computed by the graph) --
    eval_record = config.log_llm_evaluation(
        llm_result["explanation"], llm_result["llm_used"], default_rate, eval_result=graph_result["eval_result"]
    )

    # -- Step 10b: Log Prediction Batch (Delta) ----
    # This 0.5 is a separate, batch-level policy choice ("reject the whole
    # batch if more than half its individual rows look risky") -- distinct
    # from config.get_decision_threshold(), which already went into
    # computing default_rate above at the per-row level. Not a hardcoded
    # leftover to fix; a real deployment might tune this ratio too, but
    # that's a portfolio-level risk-appetite call, not a model calibration one.
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
        "warnings": (
            [f"Column(s) not found in input, defaulted to 0 for every row: {', '.join(missing_features)}"]
            if missing_features else []
        ),
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
        return _error(503, "Baseline data not loaded.")

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
    """Return info about loaded models, with real metrics from the last
    scripts/train.py run (config.MODEL_METRICS, mirrored locally from MLflow
    -- see model_loader.load_model_metrics)."""
    models = []
    champion_metrics = config.MODEL_METRICS.get("champion", {})
    challenger_metrics = config.MODEL_METRICS.get("challenger", {})
    if config.MODEL is not None:
        models.append({
            "model_id": "champion-home-credit",
            "version": "v1.0",
            "type": "champion",
            "status": "active",
            "training_date": champion_metrics.get("trained_at", "Pre-trained"),
            "metrics": {
                "auc": champion_metrics.get("auc"),
                "precision": champion_metrics.get("precision"),
                "recall": champion_metrics.get("recall"),
                "f1": champion_metrics.get("f1"),
            },
        })
    if config.GERMAN_MODEL is not None:
        models.append({
            "model_id": "challenger-german-credit",
            "version": "v1.0",
            "type": "challenger",
            "status": "standby",
            "training_date": challenger_metrics.get("trained_at", "Pre-trained"),
            "metrics": {
                "auc": challenger_metrics.get("auc"),
                "precision": challenger_metrics.get("precision"),
                "recall": challenger_metrics.get("recall"),
                "f1": challenger_metrics.get("f1"),
            },
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
