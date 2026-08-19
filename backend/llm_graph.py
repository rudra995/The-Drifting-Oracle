"""
LangGraph orchestration -- predict -> explain -> evaluate (Phase 5)
======================================================================

Wraps llm_explanation.generate_explanation/generate_batch_explanation and
llm_evaluator.evaluate_explanation as a small graph with a conditional
retry: if the RAG grounding check flags a hallucination, the graph loops
back and asks the LLM again, this time with feedback describing exactly
what was flagged, up to MAX_RETRIES times.

Retries are deliberately capped low (not unlimited): live testing against
a real local model (qwen2.5-coder:7b via Ollama, standing in as "Llama")
showed it will happily fabricate a *different* plausible-looking circular
number on request rather than stop fabricating -- so more attempts mostly
buy more chances at a new fabrication, not a guaranteed clean one. The
graph gives up after MAX_RETRIES and returns the last attempt honestly,
hallucination flag intact, rather than silently retrying forever or
hiding the failure.
"""
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from llm_explanation import generate_batch_explanation, generate_explanation
from llm_evaluator import evaluate_explanation

MAX_RETRIES = 1  # 1 retry => 2 attempts total


class ExplanationState(TypedDict):
    mode: Literal["single", "batch"]
    prediction: float  # probability (single) or default_rate (batch), 0-1
    psi: float
    psi_status: str
    explanation: str
    llm_used: str
    eval_result: dict
    attempts: int
    retry_feedback: str | None


def _explain_node(state: ExplanationState) -> dict:
    feedback = state.get("retry_feedback")
    if state["mode"] == "single":
        result = generate_explanation(state["prediction"], state["psi"], state["psi_status"], retry_feedback=feedback)
    else:
        result = generate_batch_explanation(state["prediction"], state["psi"], state["psi_status"], retry_feedback=feedback)
    return {
        "explanation": result["explanation"],
        "llm_used": result["llm_used"],
        "attempts": state["attempts"] + 1,
    }


def _evaluate_node(state: ExplanationState) -> dict:
    if state["llm_used"] == "fallback_error":
        # Both Llama and Gemini failed -- nothing to ground-check, and
        # retrying won't help since neither LLM produced any text at all.
        eval_result = {
            "grounded": False,
            "hallucination": True,
            "grounding_score": 0.0,
            "unsupported_claims": [{"claim": "LLM failed to generate explanation", "score": 0.0}],
        }
    else:
        eval_result = evaluate_explanation(state["explanation"], known_probability=state["prediction"])
    return {"eval_result": eval_result}


def _should_retry(state: ExplanationState) -> str:
    if (
        state["eval_result"]["hallucination"]
        and state["llm_used"] != "fallback_error"
        and state["attempts"] <= MAX_RETRIES
    ):
        return "retry"
    return "done"


def _prepare_retry_node(state: ExplanationState) -> dict:
    claims = state["eval_result"].get("unsupported_claims", [])
    lines = []
    for c in claims[:3]:  # cap feedback length -- a small local model has a short effective context
        reason = c.get("why_false") or "not verifiable against real RBI/SEBI regulations"
        lines.append(f'- "{c["claim"]}" -- {reason}')
    feedback = (
        "Your previous answer contained unverifiable or fabricated claims:\n"
        + "\n".join(lines)
        + "\nDo not invent specific circular numbers, dates, or percentages unless certain they are real. "
        "Prefer general, real concept references (e.g. risk-based underwriting, KYC requirements, "
        "data localization) over a specific citation you are not sure of."
    )
    return {"retry_feedback": feedback}


def _build_graph():
    graph = StateGraph(ExplanationState)
    graph.add_node("explain", _explain_node)
    graph.add_node("evaluate", _evaluate_node)
    graph.add_node("prepare_retry", _prepare_retry_node)

    graph.set_entry_point("explain")
    graph.add_edge("explain", "evaluate")
    graph.add_conditional_edges("evaluate", _should_retry, {"retry": "prepare_retry", "done": END})
    graph.add_edge("prepare_retry", "explain")

    return graph.compile()


_compiled_graph = _build_graph()


def run_explanation_graph(mode: Literal["single", "batch"], prediction: float, psi: float, psi_status: str) -> dict:
    """mode: "single" (prediction=probability) or "batch" (prediction=default_rate).

    Returns {explanation, llm_used, eval_result, attempts, retried}."""
    initial_state: ExplanationState = {
        "mode": mode,
        "prediction": prediction,
        "psi": psi,
        "psi_status": psi_status,
        "explanation": "",
        "llm_used": "",
        "eval_result": {},
        "attempts": 0,
        "retry_feedback": None,
    }
    final_state = _compiled_graph.invoke(initial_state)
    return {
        "explanation": final_state["explanation"],
        "llm_used": final_state["llm_used"],
        "eval_result": final_state["eval_result"],
        "attempts": final_state["attempts"],
        "retried": final_state["attempts"] > 1,
    }
