"""
Tests for llm_graph.py -- the LangGraph predict->explain->evaluate flow
with a conditional retry when the grounding check flags a hallucination.

Mocks llm_explanation.call_llama (same pattern as test_llm_explanation.py)
so no real network/Ollama call is needed, but exercises the REAL
evaluate_explanation() / ChromaDB retrieval -- the point of these tests is
the retry decision logic, which depends on real grounding scores.
"""
import llm_explanation as le
from llm_graph import MAX_RETRIES, run_explanation_graph

FABRICATED = "RBI Circular 2024-11 mandates notarized documents for all loan applicants, so this application is declined."
GROUNDED = "Declined per RBI's Digital Lending Directions requiring direct disbursal into the borrower's bank account."


def test_no_retry_when_first_attempt_is_clean(monkeypatch):
    calls = []

    def fake_llama(prompt):
        calls.append(prompt)
        return (GROUNDED, "llama")

    monkeypatch.setattr(le, "call_llama", fake_llama)
    monkeypatch.setattr(le, "call_gemini", lambda prompt: (_ for _ in ()).throw(
        AssertionError("Gemini should not be needed when Llama's first answer is clean")))

    result = run_explanation_graph("single", 0.3, 0.05, "no_drift")

    assert len(calls) == 1
    assert result["attempts"] == 1
    assert result["retried"] is False
    assert result["eval_result"]["hallucination"] is False
    assert result["explanation"] == GROUNDED


def test_retries_once_and_succeeds_on_a_clean_second_attempt(monkeypatch):
    responses = iter([FABRICATED, GROUNDED])
    calls = []

    def fake_llama(prompt):
        calls.append(prompt)
        return (next(responses), "llama")

    monkeypatch.setattr(le, "call_llama", fake_llama)

    result = run_explanation_graph("single", 0.7, 0.05, "no_drift")

    assert len(calls) == 2
    assert result["attempts"] == 2
    assert result["retried"] is True
    assert result["eval_result"]["hallucination"] is False
    assert result["explanation"] == GROUNDED
    # The retry prompt must carry feedback about what was flagged the first time
    assert "fabricated" in calls[1].lower() or "unverifiable" in calls[1].lower()
    assert "notarized" in calls[1]


def test_gives_up_after_max_retries_if_still_hallucinating(monkeypatch):
    calls = []

    def fake_llama(prompt):
        calls.append(prompt)
        return (FABRICATED, "llama")

    monkeypatch.setattr(le, "call_llama", fake_llama)

    result = run_explanation_graph("single", 0.7, 0.05, "no_drift")

    assert len(calls) == 1 + MAX_RETRIES
    assert result["attempts"] == 1 + MAX_RETRIES
    assert result["retried"] is True
    assert result["eval_result"]["hallucination"] is True  # honestly reported, not hidden


def test_no_retry_when_both_llms_fail(monkeypatch):
    monkeypatch.setattr(le, "call_llama", lambda prompt: (_ for _ in ()).throw(Exception("down")))
    monkeypatch.setattr(le, "call_gemini", lambda prompt: (_ for _ in ()).throw(Exception("down")))

    result = run_explanation_graph("single", 0.7, 0.05, "no_drift")

    assert result["attempts"] == 1  # no point retrying a total outage
    assert result["llm_used"] == "fallback_error"
    assert result["eval_result"]["hallucination"] is True


def test_batch_mode_works_the_same_way(monkeypatch):
    responses = iter([FABRICATED, GROUNDED])
    monkeypatch.setattr(le, "call_llama", lambda prompt: (next(responses), "llama"))

    result = run_explanation_graph("batch", 0.55, 0.1, "no_drift")

    assert result["attempts"] == 2
    assert result["eval_result"]["hallucination"] is False
