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
from llm_evaluator import valid_collection

RETRIEVAL_K = 4


def _retrieve_context(query: str) -> str:
    """
    Retrieve real regulations from the same ChromaDB corpus llm_evaluator.py
    audits against, and format them for injection into the generation
    prompt -- true retrieval-AUGMENTED generation, not just post-hoc
    retrieval-checked generation.

    Why this exists: without this, the model generates an explanation with
    zero knowledge of what's actually in the corpus, then a separate step
    checks it after the fact. Live testing showed that blind-generate ->
    check produces a real generated explanation that passes grounding
    approximately never -- the model defaults to a vague "per RBI
    guidelines" gesture with no specific citation, which correctly fails
    the check every time. Handing it real candidate regulations up front
    gives it something true to actually cite.
    """
    if valid_collection is None:
        return "(no regulation corpus available -- do not cite a specific circular or rule number)"
    try:
        hits = valid_collection.query(query_texts=[query], n_results=RETRIEVAL_K)
    except Exception:
        return "(no regulation corpus available -- do not cite a specific circular or rule number)"

    lines = []
    metadatas = hits.get("metadatas", [[]])[0]
    documents = hits.get("documents", [[]])[0]
    for meta, rule_text in zip(metadatas, documents):
        title = meta.get("title", "")
        source = meta.get("source", "")
        citation = meta.get("citation", "")
        ref = f"{source} ({citation})" if citation else source
        lines.append(f'- "{title}" -- {rule_text} [{ref}]')
    return "\n".join(lines) if lines else "(no matching regulation found -- do not cite a specific circular or rule number)"


def generate_explanation(prediction: float, psi: float, psi_status: str, retry_feedback: str = None) -> dict:
    """
    Generate explainable AI explanation for a single prediction.

    Tries Llama first, falls back to Gemini on error.

    Args:
        prediction: Probability score (0-1)
        psi: Population Stability Index
        psi_status: "drift_detected" or "no_drift"
        retry_feedback: When set (by llm_graph.py's retry loop), appended to
            the prompt describing what was flagged in a previous attempt, so
            the model can correct itself instead of repeating the mistake.

    Returns:
        {
            "explanation": str - The explanation text
            "llm_used": str - Which LLM was used ("llama", "gemini", or "fallback_error")
            "error": None or str - Error message if any
        }
    """
    decision = format_decision(prediction)
    reliability = format_reliability_status(psi_status)
    context = _retrieve_context(f"regulatory basis to {decision.lower()} a loan based on default risk assessment")

    prompt = SINGLE_PREDICTION_PROMPT_TEMPLATE.format(
        prediction=prediction,
        decision=decision,
        psi=psi,
        reliability=reliability,
        context=context,
    )
    if retry_feedback:
        prompt = f"{prompt}\n\n{retry_feedback}"

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


def generate_batch_explanation(default_rate: float, psi: float, psi_status: str, retry_feedback: str = None) -> dict:
    """
    Generate explainable AI explanation for batch predictions.

    Tries Llama first, falls back to Gemini on error.

    Args:
        default_rate: Batch default rate (0-1)
        psi: Population Stability Index
        psi_status: "drift_detected" or "no_drift"
        retry_feedback: See generate_explanation().

    Returns:
        {
            "explanation": str - The explanation text
            "llm_used": str - Which LLM was used ("llama", "gemini", or "fallback_error")
            "error": None or str - Error message if any
        }
    """
    batch_decision = format_batch_decision(default_rate)
    reliability = format_reliability_status(psi_status)
    context = _retrieve_context(f"regulatory basis to {batch_decision.lower()} a batch of loans based on portfolio default risk")

    prompt = BATCH_PREDICTION_PROMPT_TEMPLATE.format(
        default_rate=default_rate,
        psi=psi,
        reliability=reliability,
        batch_decision=batch_decision,
        context=context,
    )
    if retry_feedback:
        prompt = f"{prompt}\n\n{retry_feedback}"

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
