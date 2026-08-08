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

Probability: {prediction:.1%} ({decision})
Data Reliability: {reliability}

Provide a single-line technical assessment (1 sentence max):
- Is the system's prediction reliable for this application?
- Any data concerns or red flags?

Be direct and concise."""


BATCH_PREDICTION_PROMPT_TEMPLATE = """Batch Loan Risk Analysis

Default Rate: {default_rate:.1%}
Data Reliability: {reliability}
Batch Decision: {batch_decision}

Single-line technical summary (1 sentence max):
- Is the batch safe to process?
- Any systemic risks detected?

Direct and actionable only."""


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
