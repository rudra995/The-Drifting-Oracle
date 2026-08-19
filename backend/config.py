"""
Configuration constants for The Drifting Oracle backend.
Centralizes all tunable values in one place.

Architecture:
  - PSI now compares INCOMING CSV vs BASELINE across >=5 numeric features
  - No rolling window -- each batch is compared against the training distribution
  - Model switching: PSI < 0.25 -> Champion, else -> Challenger
"""
import os
from datetime import datetime, timezone

import databricks_io

# --------------------------------------------
# Model Paths (case-insensitive fallbacks)
# --------------------------------------------
MODEL_PATHS = ["models/model.pkl", "Models/model.pkl"]
GERMAN_MODEL_PATHS = ["models/model_german.pkl", "Models/model_german.pkl"]
MODEL_METRICS_PATHS = ["models/model_metrics.json", "Models/model_metrics.json"]
FEATURE_PATHS = ["models/features.txt", "Models/features.txt"]
BASELINE_PATHS = [
    "models/baseline.csv",
    "Models/baseline.csv",
    "dataset/raw/application_train.csv",
    # Last-resort fallback only -- cleaned_data.csv has EXT_SOURCE_3 (and
    # possibly other EXT_SOURCE) missing values imputed to a literal 0.0,
    # while live serving (psi.py) drops true NaNs. That mismatch causes a
    # large false-positive PSI spike on any real batch with normal (~19%)
    # missingness in that feature -- confirmed live: PSI 0.40 -> 0.05 on the
    # same 2,000-row real batch once the baseline source was switched to the
    # raw, unimputed file above, which is processed through the identical
    # reshape/engineer path a live batch goes through.
    "dataset/cleaned_data.csv",
]

# --------------------------------------------
# PSI Configuration -- Multi-Feature
# --------------------------------------------
# Key numeric features used for PSI drift detection (>=5 required by spec)
PSI_FEATURES = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT_x",
    "AMT_ANNUITY",
    "DAYS_EMPLOYED",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "income_credit_ratio",
]

PSI_NUM_BINS = 10

# --------------------------------------------
# Why 0.25?
# --------------------------------------------
# PSI is a sum of (actual% - expected%) * ln(actual% / expected%) across bins,
# so it's an unbounded, feature-scale-independent measure of how far an
# incoming distribution has drifted from the training baseline. The bands
# below are the standard credit-risk-industry interpretation of PSI, not
# specific to this project -- they come from Population Stability Index's
# original use in credit scorecard monitoring (SAS/FICO literature), and the
# same bands are what Home Credit / SEBI-style risk teams use in practice:
#
#   PSI < 0.10            -> no meaningful shift. Model is safe as-is.
#   0.10 <= PSI < 0.25     -> moderate shift. Worth investigating, not yet
#                             an action trigger -- could be noise or a small,
#                             recoverable seasonal effect.
#   PSI >= 0.25            -> significant shift. The scoring population has
#                             materially diverged from what the model was
#                             trained on; treat predictions as unreliable
#                             until addressed.
#
# 0.25 is set as the single action threshold (not 0.10) deliberately: it's
# the point where the standard interpretation stops calling the shift
# "moderate" and starts calling it "significant." Below it, switching models
# or retraining on every minor fluctuation would cause far more churn
# (and far more retraining cost -- see retrain.py's cooldown) than the drift
# actually warrants. A lower threshold trades false-alarm rate for
# sensitivity; 0.25 is the industry's usual line for "this needs a response,"
# not a value tuned to this specific dataset.
#
# Overall PSI here is the mean of the per-feature PSI scores (psi.py), so a
# single wildly-drifted feature can't single-handedly trigger the threshold
# on its own unless it dominates the average -- multiple features drifting
# together is what actually crosses 0.25 in practice.
PSI_THRESHOLD = 0.25  # Single threshold: < 0.25 = Champion, >= 0.25 = Challenger + retrain

# --------------------------------------------
# Risk Label Thresholds
# --------------------------------------------
RISK_LOW_THRESHOLD = 0.3       # probability < 0.3 -> "Low"
RISK_HIGH_THRESHOLD = 0.7      # probability >= 0.7 -> "High"
                                # 0.3 <= probability < 0.7 -> "Medium"

DEFAULT_DECISION_THRESHOLD = 0.5  # sklearn's default -- used only as a
                                   # fallback before scripts/tune_threshold.py
                                   # has ever been run for this model.


def get_decision_threshold() -> float:
    """
    The Accept/Reject cutoff on predicted default probability. Reads
    champion.decision_threshold from Models/model_metrics.json (written by
    scripts/tune_threshold.py, cost-weighted -- see that script's docstring
    for why this isn't a bare 0.5 or F1-argmax), falling back to 0.5 if
    tuning has never been run. A function, not a module-level constant,
    because MODEL_METRICS is only populated after config.py is imported
    (at server startup, via model_loader.load_model_metrics()).
    """
    return MODEL_METRICS.get("champion", {}).get("decision_threshold", DEFAULT_DECISION_THRESHOLD)


# --------------------------------------------
# Auth -- minimal shared-secret API key
# --------------------------------------------
# Unset by default so local dev/CI/tests need no configuration -- matches
# every other credential in this project (Databricks, Gemini) being an
# opt-in .env value, not a hardcoded requirement. Set API_KEY to actually
# require the X-API-Key header (see main.py's require_api_key middleware);
# this is a portfolio-appropriate minimal gate, not a real user-auth system
# with accounts/sessions -- see docs/interview-prep.pdf's known limitations
# for why that scope boundary is deliberate.
API_KEY = os.getenv("API_KEY") or None

# --------------------------------------------
# Champion -> Challenger Feature Mapping
# Maps Home Credit columns to German model features
# --------------------------------------------
CHAMPION_TO_CHALLENGER_MAP = {
    "Income":           "AMT_INCOME_TOTAL",
    "LoanAmount":       "AMT_CREDIT_x",
    "Age":              "age",               # Engineered feature
    "EmploymentYears":  "DAYS_EMPLOYED",     # Needs transformation: abs(days)/365
    "income_loan_ratio": "income_credit_ratio",
}
# CreditScore, DTI, loan_dti_ratio -> derived/default (no direct mapping)

# --------------------------------------------
# Global Mutable State
# --------------------------------------------
MODEL = None                          # Champion model (XGBClassifier, 20 features)
GERMAN_MODEL = None                   # Challenger model (XGBClassifier, 8 features)
MODEL_METRICS: dict = {}              # {"champion": {auc, precision, recall, f1, model_type, trained_at}, "challenger": {...}}
FEATURE_ORDER: list[str] = []         # Champion feature names from features.txt
BASELINE_DATA = None                  # Full baseline DataFrame (training distribution)
BASELINE_DISTRIBUTIONS: dict = {}     # {feature_name: np.ndarray of bin percentages}
BASELINE_BINS: dict = {}              # {feature_name: np.ndarray of bin edges}

# --------------------------------------------
# Tracking State (for dashboard / governance)
# --------------------------------------------
PREDICTION_COUNT = 0
DRIFT_COUNT = 0
DRIFT_HISTORY: list[dict] = []
GOVERNANCE_LOG: list[dict] = []
LLM_EVALUATIONS: list[dict] = []

# --------------------------------------------
# Retraining State (Phase 2 -- drift-triggered retrain)
# --------------------------------------------
LAST_RETRAIN_TRIGGERED_AT: float = 0.0
RETRAIN_COOLDOWN_SECONDS: int = 600  # 10 min -- don't spawn a retrain per drifted batch
RETRAIN_IN_PROGRESS: bool = False


def log_governance_event(event_type: str, details: str, model_id: str = None):
    """Append a governance event to the in-memory log and persist it to Delta."""
    GOVERNANCE_LOG.insert(0, {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event_type": event_type,
        "details": details,
        "model_id": model_id,
    })
    databricks_io.insert_governance_event(event_type, details, model_id)


def log_drift_detection(overall_psi: float, per_feature: dict, drift_detected: bool):
    """Record a drift detection result with per-feature breakdown, in-memory and in Delta."""
    recommendation = (
        "Switch to Challenger model -- significant distribution shift detected."
        if drift_detected
        else "No action required -- data distribution stable."
    )
    DRIFT_HISTORY.insert(0, {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "overall_psi": overall_psi,
        "drift_detected": drift_detected,
        "drift_features": [
            {"feature_name": feat, "psi_score": score}
            for feat, score in per_feature.items()
        ],
        "recommendation": recommendation,
    })
    databricks_io.insert_drift_event(overall_psi, per_feature, drift_detected, recommendation)


def log_llm_evaluation(explanation: str, llm_used: str, probability: float = None, eval_result: dict = None):
    """
    Log an LLM-generated explanation for evaluation and monitoring using semantic embedding auditing.

    eval_result: pass this through when the caller already ran the grounding
    check (llm_graph.py's predict->explain->evaluate graph always has, since
    it needs the result to decide whether to retry) -- avoids re-running the
    embedding + ChromaDB lookup a second time for the same explanation.
    """
    import config

    if eval_result is not None:
        pass  # already computed by the caller (llm_graph.py)
    elif llm_used == "fallback_error":
        # Fast fallback if explanation errored gracefully before LLM
        eval_result = {
            "grounded": False,
            "hallucination": True,
            "grounding_score": 0.0,
            "unsupported_claims": [{"claim": "LLM failed to generate explanation", "score": 0.0}]
        }
    else:
        # Import dynamically to avoid circular issues during startup
        try:
            from llm_evaluator import evaluate_explanation
            eval_result = evaluate_explanation(explanation, known_probability=probability)
        except Exception as e:
            print("LLM EVALUATOR ERROR:", repr(e))
            import traceback
            traceback.print_exc()
            eval_result = {
                "grounded": False,
                "hallucination": False,
                "grounding_score": 0.0,
                "unsupported_claims": ["Evaluator completely missing"]
            }

    eval_record = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "explanation": explanation[:200],  # First 200 chars for display
        "llm_used": llm_used,
        "factual_grounding_score": eval_result["grounding_score"],
        "hallucination_score": 1.0 - eval_result["grounding_score"], # Derived metric for fallback charts
        "status": "accepted" if eval_result["grounded"] and not eval_result["hallucination"] else "rejected",
        "issues_found": [
            f"{c['claim']} \n-> EXPECTED RULE: {c['closest_rule']}" if isinstance(c, dict) and "closest_rule" in c
            else c["claim"] if isinstance(c, dict) else c 
            for c in eval_result.get("unsupported_claims", [])
        ],
        "evaluation": eval_result
    }
    
    config.LLM_EVALUATIONS.insert(0, eval_record)

    databricks_io.insert_llm_evaluation(
        eval_record["explanation"],
        eval_record["llm_used"],
        eval_record["factual_grounding_score"],
        eval_record["hallucination_score"],
        eval_record["status"],
        eval_record["issues_found"],
    )

    # Keep only last 50 evaluations in memory (Delta table keeps full history)
    if len(config.LLM_EVALUATIONS) > 50:
        config.LLM_EVALUATIONS.pop()

    return eval_record
