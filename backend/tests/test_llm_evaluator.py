"""
Labeled regression tests for llm_evaluator.py's ChromaDB-backed RAG
grounding/hallucination check (Phase 5 of the remediation roadmap).

These cases exist because manual spot-checking during development found two
real, non-obvious failure modes that a naive implementation gets wrong:

  1. Pure semantic similarity is numerically blind -- "risk weight is 125%"
     and "risk weight is 150%" embed almost identically, so a claim citing
     a materially wrong number (10% DLG cap instead of the real 5%) was
     scoring as "grounded" purely because the surrounding sentence read as
     topically correct. See the cap/floor/exact cases below.

  2. Not every regulatory number is violated the same way. RBI's risk
     weight rule is a FLOOR ("125% or higher") -- citing a higher figure is
     still compliant. The DLG rule is a hard CAP -- citing a higher figure
     is a violation. Treating every mismatch as "any different number is
     wrong" produces false positives on legitimate floor claims (a first
     implementation attempt here did exactly that for the 150% case below,
     before the cap/floor/exact typing was added).

Each case is (explanation_text, expected_hallucination_flag). Real model
calls -- no mocking of the embedder or ChromaDB, since the point is to
exercise the actual retrieval + numeric-conflict logic end to end.
"""
import pytest

from llm_evaluator import evaluate_explanation


CASES = [
    # -- Real, correctly-cited regulations (should NOT flag) --
    (
        "correct floor value (125%, at the minimum)",
        "Risk weight on unsecured personal loans has been increased to 125 percent under RBI capital regulations.",
        False,
    ),
    (
        "floor satisfied by a higher value (150% -- RBI's own text says '125% or higher')",
        "Risk weight on unsecured personal loans has been increased to 150 percent under RBI capital regulations.",
        False,
    ),
    (
        "cap satisfied (3% DLG, under the real 5% cap)",
        "Default Loss Guarantee cover is limited to 3 percent of the disbursed loan portfolio under RBI digital lending rules.",
        False,
    ),
    (
        "grounded claim with no numbers to check",
        "Declined per RBI Digital Lending Directions requiring enhanced KYC and risk-based underwriting.",
        False,
    ),

    # -- Numerically wrong (should flag, via the cap/floor/exact conflict check) --
    (
        "floor violated (80%, below the real 125% minimum)",
        "Risk weight on unsecured personal loans has been set at 80 percent under RBI capital regulations.",
        True,
    ),
    (
        "cap violated (10% DLG, above the real 5% cap)",
        "Default Loss Guarantee cover is capped at 10 percent of the disbursed loan portfolio under RBI digital lending rules.",
        True,
    ),
    (
        "exact cutoff violated (20% NPA threshold, real cutoff is 10%)",
        "Assets with realizable security value below 20 percent of the outstanding balance must be classified as loss assets per RBI norms.",
        True,
    ),
    (
        "floor violated (3-year KYC retention, real minimum is 5 years)",
        "KYC records must be retained for 3 years after the account relationship ends per RBI rules.",
        True,
    ),
    (
        "cap violated (48-hour data repatriation, real cap is 24 hours)",
        "If borrower data is processed abroad it must be deleted and repatriated to India within 48 hours per RBI digital lending rules.",
        True,
    ),

    # -- Known-fabricated claims (should flag via the invalid-examples collection) --
    (
        "invented circular number",
        "RBI Circular 2024-11 mandates notarized documents for all loan applicants, so this application is declined.",
        True,
    ),
    (
        "SEBI has no jurisdiction over personal lending",
        "SEBI prohibits NBFCs from offering personal loans below 12% interest rate, so this loan is declined.",
        True,
    ),

    # -- Off-topic text (should flag -- nothing regulation-shaped to ground) --
    (
        "generic reliability sentence, not a regulatory claim at all",
        "The prediction is reliable given stable feature distributions; no immediate red flags.",
        True,
    ),
]


@pytest.mark.parametrize("label,text,expected_flag", CASES, ids=[c[0] for c in CASES])
def test_hallucination_flag(label, text, expected_flag):
    result = evaluate_explanation(text)
    assert result["hallucination"] == expected_flag, (
        f"[{label}] expected hallucination={expected_flag}, got {result['hallucination']} "
        f"(grounding_score={result['grounding_score']}, claims={result['unsupported_claims']})"
    )


def test_empty_explanation_is_flagged():
    result = evaluate_explanation("")
    assert result["hallucination"] is True
    assert result["grounding_score"] == 0.0


def test_grounded_claim_carries_real_citation_metadata():
    """A cleanly-grounded claim should surface a real source/citation/URL,
    not just a bare pass/fail -- that's the whole point of using RAG over
    real regulation text instead of a fixed hardcoded list."""
    result = evaluate_explanation(
        "Loan disbursement must be made directly into the borrower's bank account per RBI rules."
    )
    assert result["hallucination"] is False
