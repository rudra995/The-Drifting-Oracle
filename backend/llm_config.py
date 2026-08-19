"""
LLM Configuration and Prompt Templates
=======================================

Centralized configuration for Llama and Gemini LLMs.
Includes endpoint settings, model names, and prompt templates.
"""

import os

# ============================================================================
# LLAMA CONFIGURATION
# ============================================================================

LLAMA_ENDPOINT = os.getenv("LLAMA_ENDPOINT", "http://localhost:11434/api/generate")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama2")
LLAMA_TIMEOUT = 30  # seconds
LLAMA_TEMPERATURE = 0.3


# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3-flash-preview"
# Note: Gemini 3 models work best with default temperature (1.0)
# Using 0.3 for deterministic/consistent responses in our use case
GEMINI_TEMPERATURE = 0.3
GEMINI_MAX_TOKENS = 300


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SINGLE_PREDICTION_PROMPT_TEMPLATE = """Loan Application Risk Assessment

Probability of Default: {prediction:.1%} ({decision})
Data Reliability: {reliability}

Real regulations retrieved from the compliance database (cite ONE of these
by paraphrasing it in your own words -- do not invent a different circular
number, date, or percentage than what is shown here):
{context}

State the regulatory justification for this decision as ONE terse, factual
sentence, paraphrasing ONE of the regulations listed above -- name what it's
about (e.g. "risk-based underwriting", "the Fair Practices Code") rather
than inventing a circular/citation number of your own. If none of the
regulations above genuinely fit this decision, say the decision follows
standard risk-based underwriting practice rather than inventing a specific
citation. Mention data reliability only if it is a concern. The percentage
above is a probability of DEFAULT (risk of non-repayment), not a probability
of approval -- do not restate it as "probability of approval" or similar.

Do NOT include a greeting, an apology, a closing pleasantry, or filler such
as "we appreciate your understanding" or "thank you" -- output only the
factual justification sentence itself, nothing else."""


BATCH_PREDICTION_PROMPT_TEMPLATE = """Batch Loan Risk Analysis

Default Rate: {default_rate:.1%}
Data Reliability: {reliability}
Batch Decision: {batch_decision}

Real regulations retrieved from the compliance database (cite ONE of these
by paraphrasing it in your own words -- do not invent a different circular
number, date, or percentage than what is shown here):
{context}

State the regulatory justification for this batch decision as ONE terse,
factual sentence, paraphrasing ONE of the regulations listed above -- name
what it's about (e.g. "risk-based underwriting", "portfolio risk limits")
rather than inventing a circular/citation number of your own. If none of the
regulations above genuinely fit, say the decision follows standard
portfolio risk management practice rather than inventing a specific
citation. Mention systemic risk or data reliability only if it is a concern.

Do NOT include a greeting, an apology, a closing pleasantry, or any filler --
output only the factual justification sentence itself, nothing else."""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_reliability_status(psi_status: str) -> str:
    """Convert PSI status to human-readable reliability message."""
    if psi_status == "drift_detected":
        return "UNRELIABLE (drift detected)"
    return "RELIABLE (normal)"


def format_decision(probability: float) -> str:
    """Convert probability to decision label."""
    return "REJECT Loan" if probability >= 0.5 else "APPROVE Loan"


def format_batch_decision(default_rate: float) -> str:
    """Convert default rate to batch decision label."""
    return "REJECT Batch" if default_rate >= 0.5 else "APPROVE Batch"
