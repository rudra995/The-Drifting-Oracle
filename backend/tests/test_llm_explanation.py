"""
Tests for the Llama -> Gemini -> fallback_error resilience chain in
llm_explanation.py. No real network calls -- call_llama/call_gemini are
mocked, since a CI runner has neither a local Ollama instance nor should
depend on a live paid Gemini key to pass.
"""
import pytest

import llm_explanation as le


def test_uses_llama_when_it_succeeds(monkeypatch):
    monkeypatch.setattr(le, "call_llama", lambda prompt: ("Llama says approve.", "llama"))
    monkeypatch.setattr(le, "call_gemini", lambda prompt: (_ for _ in ()).throw(
        AssertionError("Gemini should not be called when Llama succeeds")))

    result = le.generate_explanation(0.2, 0.05, "no_drift")

    assert result["llm_used"] == "llama"
    assert result["explanation"] == "Llama says approve."
    assert result["error"] is None


def test_falls_back_to_gemini_when_llama_fails(monkeypatch):
    def broken_llama(prompt):
        raise Exception("Llama endpoint unreachable")

    monkeypatch.setattr(le, "call_llama", broken_llama)
    monkeypatch.setattr(le, "call_gemini", lambda prompt: ("Gemini says reject.", "gemini"))

    result = le.generate_explanation(0.9, 0.3, "drift_detected")

    assert result["llm_used"] == "gemini"
    assert result["explanation"] == "Gemini says reject."
    assert result["error"] is None


def test_returns_fallback_error_when_both_llms_fail(monkeypatch):
    monkeypatch.setattr(le, "call_llama", lambda prompt: (_ for _ in ()).throw(Exception("down")))
    monkeypatch.setattr(le, "call_gemini", lambda prompt: (_ for _ in ()).throw(Exception("down")))

    result = le.generate_explanation(0.5, 0.1, "no_drift")

    assert result["llm_used"] == "fallback_error"
    assert result["error"] is not None
    assert result["explanation"] == result["error"]


def test_batch_explanation_follows_the_same_fallback_chain(monkeypatch):
    monkeypatch.setattr(le, "call_llama", lambda prompt: (_ for _ in ()).throw(Exception("down")))
    monkeypatch.setattr(le, "call_gemini", lambda prompt: ("Batch summary from Gemini.", "gemini"))

    result = le.generate_batch_explanation(0.4, 0.15, "no_drift")

    assert result["llm_used"] == "gemini"
    assert result["explanation"] == "Batch summary from Gemini."


def test_prompt_includes_the_prediction_and_reliability_status(monkeypatch):
    """Note: the prompt template embeds the *derived* reliability label
    (RELIABLE/UNRELIABLE), not the raw PSI number itself -- PSI only feeds
    format_reliability_status() before reaching the template."""
    captured = {}

    def capturing_llama(prompt):
        captured["prompt"] = prompt
        return ("ok", "llama")

    monkeypatch.setattr(le, "call_llama", capturing_llama)

    le.generate_explanation(0.83, 0.42, "drift_detected")

    assert "83.0%" in captured["prompt"]
    assert "REJECT Loan" in captured["prompt"]
    assert "UNRELIABLE" in captured["prompt"]
