"""
LLM Explanation Layer
=====================

High-level explanation generation for predictions and drift detection.
Uses Llama as primary LLM, Gemini as fallback.

Orchestrates:
  - Single prediction explanations
  - Batch default rate explanations
  - Fallback mechanism for resilience

Reference: https://ai.google.dev/gemini-api/docs
"""

from llm_clients import call_llama, call_gemini
from llm_config import (
    SINGLE_PREDICTION_PROMPT_TEMPLATE,
    BATCH_PREDICTION_PROMPT_TEMPLATE,
    format_reliability_status,
    format_decision,
    format_batch_decision,
)


def generate_explanation(prediction: float, psi: float, psi_status: str) -> dict:
    """
    Generate explainable AI explanation for a single prediction.
    
    Tries Llama first, falls back to Gemini on error.
    
    Args:
        prediction: Probability score (0-1)
        psi: Population Stability Index
        psi_status: "drift_detected" or "no_drift"
    
    Returns:
        {
            "explanation": str - The explanation text
            "llm_used": str - Which LLM was used ("llama", "gemini", or "fallback_error")
            "error": None or str - Error message if any
        }
    """
    decision = format_decision(prediction)
    reliability = format_reliability_status(psi_status)
    
    prompt = SINGLE_PREDICTION_PROMPT_TEMPLATE.format(
        prediction=prediction,
        decision=decision,
        psi=psi,
        reliability=reliability,
    )
    
    explanation_text = None
    llm_used = None
    error = None
    
    # Try Llama first
    try:
        explanation_text, llm_used = call_llama(prompt)
        return {
            "explanation": explanation_text,
            "llm_used": llm_used,
            "error": None,
        }
    except Exception as e:
        print(f"[LLM] Llama primary failed, attempting Gemini fallback...")
    
    # Fallback to Gemini
    try:
        explanation_text, llm_used = call_gemini(prompt)
        return {
            "explanation": explanation_text,
            "llm_used": llm_used,
            "error": None,
        }
    except Exception as gemini_error:
        print(f"[LLM] Gemini fallback failed: {str(gemini_error)}")
        error = "Unable to generate explanation at this time."
        return {
            "explanation": error,
            "llm_used": "fallback_error",
            "error": error,
        }


def generate_batch_explanation(default_rate: float, psi: float, psi_status: str) -> dict:
    """
    Generate explainable AI explanation for batch predictions.
    
    Tries Llama first, falls back to Gemini on error.
    
    Args:
        default_rate: Batch default rate (0-1)
        psi: Population Stability Index
        psi_status: "drift_detected" or "no_drift"
    
    Returns:
        {
            "explanation": str - The explanation text
            "llm_used": str - Which LLM was used ("llama", "gemini", or "fallback_error")
            "error": None or str - Error message if any
        }
    """
    batch_decision = format_batch_decision(default_rate)
    reliability = format_reliability_status(psi_status)
    
    prompt = BATCH_PREDICTION_PROMPT_TEMPLATE.format(
        default_rate=default_rate,
        psi=psi,
        reliability=reliability,
        batch_decision=batch_decision,
    )
    
    explanation_text = None
    llm_used = None
    error = None
    
    # Try Llama first
    try:
        explanation_text, llm_used = call_llama(prompt)
        return {
            "explanation": explanation_text,
            "llm_used": llm_used,
            "error": None,
        }
    except Exception as e:
        print(f"[LLM] Llama primary failed, attempting Gemini fallback...")
    
    # Fallback to Gemini
    try:
        explanation_text, llm_used = call_gemini(prompt)
        return {
            "explanation": explanation_text,
            "llm_used": llm_used,
            "error": None,
        }
    except Exception as gemini_error:
        print(f"[LLM] Gemini fallback failed: {str(gemini_error)}")
        error = "Unable to generate explanation at this time."
        return {
            "explanation": error,
            "llm_used": "fallback_error",
            "error": error,
        }
