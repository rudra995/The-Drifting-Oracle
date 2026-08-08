"""
Configuration constants for The Drifting Oracle backend.
Centralizes all tunable values in one place.

Architecture:
  - PSI now compares INCOMING CSV vs BASELINE across >=5 numeric features
  - No rolling window -- each batch is compared against the training distribution
  - Model switching: PSI < 0.25 -> Champion, else -> Challenger
"""
from datetime import datetime

# --------------------------------------------
# Model Paths (case-insensitive fallbacks)
# --------------------------------------------
MODEL_PATHS = ["models/model.pkl", "Models/model.pkl"]
GERMAN_MODEL_PATHS = ["models/model_german.pkl", "Models/model_german.pkl"]
FEATURE_PATHS = ["models/features.txt", "Models/features.txt"]
BASELINE_PATHS = [
    "models/baseline.csv",
    "Models/baseline.csv",
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
PSI_THRESHOLD = 0.25  # Single threshold: < 0.25 = Champion, >= 0.25 = Challenger

# --------------------------------------------
# Risk Label Thresholds
# --------------------------------------------
RISK_LOW_THRESHOLD = 0.3       # probability < 0.3 -> "Low"
RISK_HIGH_THRESHOLD = 0.7      # probability >= 0.7 -> "High"
                                # 0.3 <= probability < 0.7 -> "Medium"

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


def log_governance_event(event_type: str, details: str, model_id: str = None):
    """Append a governance event to the in-memory log."""
    GOVERNANCE_LOG.insert(0, {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "details": details,
        "model_id": model_id,
    })


def log_drift_detection(overall_psi: float, per_feature: dict, drift_detected: bool):
    """Record a drift detection result with per-feature breakdown."""
    DRIFT_HISTORY.insert(0, {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "overall_psi": overall_psi,
        "drift_detected": drift_detected,
        "drift_features": [
            {"feature_name": feat, "psi_score": score}
            for feat, score in per_feature.items()
        ],
        "recommendation": (
            "Switch to Challenger model -- significant distribution shift detected."
            if drift_detected
            else "No action required -- data distribution stable."
        ),
    })


def log_llm_evaluation(explanation: str, llm_used: str, probability: float = None):
    """
    Log an LLM-generated explanation for evaluation and monitoring using semantic embedding auditing.
    """
    from datetime import datetime
    import config
    
    # Fast fallback if explanation errored gracefully before LLM
    if llm_used == "fallback_error":
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
            eval_result = evaluate_explanation(explanation)
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
        "timestamp": datetime.utcnow().isoformat() + "Z",
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
    
    # Keep only last 50 evaluations to prevent memory bloat
    if len(config.LLM_EVALUATIONS) > 50:
        config.LLM_EVALUATIONS.pop()
        
    return eval_record
