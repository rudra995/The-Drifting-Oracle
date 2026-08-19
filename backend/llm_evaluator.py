import json
import os
import re

# Redirect HF model cache to D: drive (C: may not have enough space for model weights)
os.environ.setdefault("HF_HOME", r"D:\hackbricks\hf_cache")

from scripts.setup_chromadb import ensure_collections

# ----------------------------------------------------
# STEP 1: RAG-BACKED RBI/SEBI REGULATION CORPUS
# ----------------------------------------------------
# Real, individually-sourced RBI/SEBI regulations retrieved from a local
# ChromaDB vector store (dataset/rbi_regulations_corpus.json), replacing the
# old fixed 16-item in-memory list. Two collections:
#   - valid_collection:   real regulations, top-k semantic match = grounding
#   - invalid_collection: known-fabricated claims, top-k match = hallucination
print("[LLM Evaluator] Loading ChromaDB regulation collections (all-MiniLM-L6-v2)...")
try:
    valid_collection, invalid_collection = ensure_collections()
    print(
        f"[LLM Evaluator] Ready -- {valid_collection.count()} valid regulations, "
        f"{invalid_collection.count()} known-fabricated examples."
    )
except Exception as e:
    print(f"[LLM Evaluator] Warning: Failed to load ChromaDB regulation store. {e}")
    valid_collection = None
    invalid_collection = None

# Same bands as the original design (Section 4.1 Factual Grounding Score in
# the retired rbi_sebi_ground_truth.md), now applied to Chroma's cosine
# similarity (1 - cosine distance) instead of a hand-rolled cos_sim tensor.
INVALID_MATCH_THRESHOLD = 0.75
GROUNDING_BANDS = [
    (0.80, 1.00),   # Exact/strong match
    (0.65, 0.75),   # Correct concept / partial
    (0.50, 0.50),   # Partially correct / misapplied
    (0.35, 0.25),   # Related but factually inaccurate
]
VALID_TOP_K = 3  # retrieve top-3 candidates so a numeric conflict on the
                 # best semantic match can fall back to a cleaner runner-up


def _claim_score(similarity: float) -> float:
    for min_sim, score in GROUNDING_BANDS:
        if similarity >= min_sim:
            return score
    return 0.0  # Complete hallucination


# ----------------------------------------------------
# NUMERIC FACT VERIFICATION
# ----------------------------------------------------
# Pure semantic similarity cannot tell "risk weight is 125%" apart from
# "risk weight is 150%" -- both sentences embed almost identically. Every
# regulation in the corpus that hinges on a number/percentage/duration
# carries an explicit "thresholds" list (see rbi_regulations_corpus.json),
# tagged by TYPE because not every threshold is violated the same way:
#   - "cap":   a maximum -- citing a HIGHER value is a violation
#   - "floor": a minimum -- citing a LOWER value is a violation
#   - "exact": a specific cutoff -- citing ANY different value is a violation
# (e.g. RBI's unsecured-loan risk weight is a FLOOR -- "125% or higher" --
# so a claim of 150% is still compliant; only a claim below 125% is wrong.
# The DLG cap is a hard CAP at 5% -- anything higher violates it.)
_UNIT_PATTERNS = {
    "%": r'(\d+(?:\.\d+)?)\s*(?:%|percent)',
    "day": r'(\d+(?:\.\d+)?)[\s-]*days?\b',
    "hour": r'(\d+(?:\.\d+)?)[\s-]*hours?\b',
    "month": r'(\d+(?:\.\d+)?)[\s-]*months?\b',
    "year": r'(\d+(?:\.\d+)?)[\s-]*years?\b',
}


def _extract_numeric_facts(text: str) -> dict:
    """{"unit": [values]} for every %/day/hour/month/year figure found in text."""
    facts = {}
    for unit, pattern in _UNIT_PATTERNS.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            facts[unit] = [float(m) for m in matches]
    return facts


_KNOWN_VALUE_TOLERANCE = 0.6  # percentage points -- catches "18%" vs "18.0%" rounding


def _numeric_conflict(claim: str, thresholds: list, known_percent: float | None = None) -> dict | None:
    """Check claim's numeric facts against a candidate rule's typed thresholds.
    Returns a conflict detail dict, or None if consistent / not checkable.

    known_percent, when given, is the model's OWN predicted probability or
    batch default rate (already known to the caller, since it's what the
    prompt told the LLM). Found via live testing against a real local LLM:
    the model routinely restates this number in the same sentence as a
    vague RBI namedrop ("...an 18.0% probability... per RBI guidelines"),
    and without this exclusion that restated figure gets checked as if it
    were an independent regulatory claim -- e.g. flagged as violating an
    unrelated 5% DLG cap, which is nonsense: 18% was never a claim about
    DLG at all, it's just the model echoing the probability it was given.
    """
    if not thresholds:
        return None
    claim_facts = _extract_numeric_facts(claim)
    if known_percent is not None and "%" in claim_facts:
        claim_facts["%"] = [v for v in claim_facts["%"] if abs(v - known_percent) > _KNOWN_VALUE_TOLERANCE]
        if not claim_facts["%"]:
            del claim_facts["%"]
    if not claim_facts:
        return None

    for t in thresholds:
        unit, val, ttype = t["unit"], t["value"], t["type"]
        if unit not in claim_facts:
            continue
        for cv in claim_facts[unit]:
            violated = (
                (ttype == "exact" and abs(cv - val) > 1e-6) or
                (ttype == "cap" and cv > val + 1e-6) or
                (ttype == "floor" and cv < val - 1e-6)
            )
            if violated:
                return {
                    "claimed_value": cv,
                    "unit": unit,
                    "expected_value": val,
                    "expected_type": ttype,
                }
    return None


_CONTENTION_MARGIN = 0.05  # a candidate only competes for "the topic this claim is
                            # about" if it's within this much of the best similarity


def _best_valid_candidate(claim: str, metadatas: list, distances: list, known_percent: float | None = None):
    """Score the top-k valid candidates and pick which one to report.

    Numeric conflict checking is deliberately restricted to candidates that
    are genuinely IN CONTENTION for being the rule this claim is about
    (similarity within _CONTENTION_MARGIN of the best match) -- comparing a
    claim's number against an unrelated regulation's threshold is
    meaningless (e.g. a legitimate "125%" risk-weight claim will trivially
    "violate" an unrelated 5% DLG cap just by being a bigger number; that is
    not evidence of anything). Within that contention set, a real conflict
    still must be surfaced even if it isn't the single highest-similarity
    hit, so a topically-irrelevant zero-threshold candidate can't mask it.
    """
    scored = []
    for meta, dist in zip(metadatas, distances):
        similarity = 1.0 - dist
        thresholds = json.loads(meta.get("thresholds_json") or "[]")
        scored.append((similarity, thresholds, meta))

    best_similarity = max(s[0] for s in scored)
    in_contention = [s for s in scored if s[0] >= best_similarity - _CONTENTION_MARGIN]

    conflicting = []
    for similarity, thresholds, meta in in_contention:
        conflict = _numeric_conflict(claim, thresholds, known_percent=known_percent)
        if conflict is not None:
            conflicting.append((similarity, conflict, meta))

    if conflicting:
        similarity, conflict, meta = max(conflicting, key=lambda s: s[0])
        return similarity, conflict, meta

    similarity, _, meta = max(scored, key=lambda s: s[0])
    return similarity, None, meta


# ----------------------------------------------------
# STEP 2: CLAIM EXTRACTION & TOP-K RETRIEVAL VERIFICATION
# ----------------------------------------------------
def evaluate_explanation(explanation: str, known_probability: float | None = None) -> dict:
    """known_probability: the model's own prediction (0-1) or batch default
    rate, when available -- excluded from numeric-conflict checks since the
    LLM restating a number it was explicitly given is not an independent
    regulatory claim (see _numeric_conflict's docstring)."""
    known_percent = known_probability * 100 if known_probability is not None else None

    if valid_collection is None or invalid_collection is None:
        return {
            "grounded": False,
            "hallucination": False,
            "grounding_score": 0.0,
            "unsupported_claims": [{"claim": "System Error: Regulation vector store not loaded", "score": 0.0}]
        }

    # Split on sentence-ending punctuation, but NOT a period sitting between
    # two digits -- a naive [.!?] split chops "82.0%" into "82" and "0%",
    # which then gets read as a fabricated "0%" figure by the numeric
    # conflict check below. Caught via live testing against a real local
    # LLM, whose output naturally included decimal percentages.
    raw_sentences = re.split(r'(?:(?<!\d)[.!?](?!\d))+|\n+', explanation)
    claims = [s.strip() for s in raw_sentences if len(s.strip()) > 10]

    if not claims:
        return {
            "grounded": False,
            "hallucination": True,
            "grounding_score": 0.0,
            "unsupported_claims": [{"claim": "No meaningful claims extracted.", "score": 0.0}]
        }

    # Batch retrieval: top-1 against known fabrications, top-3 against real
    # regulations (so a numeric conflict on the best match can fall back to
    # a numerically-clean runner-up instead of forcing a false positive).
    invalid_hits = invalid_collection.query(query_texts=claims, n_results=1)
    valid_hits = valid_collection.query(query_texts=claims, n_results=VALID_TOP_K)

    unsupported_claims = []
    total_grounding = 0.0
    has_hallucination = False

    for i, claim in enumerate(claims):
        # 1. Semantic match against KNOWN FABRICATED regulations
        inv_distance = invalid_hits["distances"][i][0]
        inv_similarity = 1.0 - inv_distance
        if inv_similarity > INVALID_MATCH_THRESHOLD:
            inv_meta = invalid_hits["metadatas"][i][0]
            has_hallucination = True
            unsupported_claims.append({
                "claim": f"{claim} (KNOWN HALLUCINATION FLAG)",
                "closest_rule": inv_meta["true_rule"],
                "why_false": inv_meta["why_false"],
                "score": 0.0
            })
            continue

        # 2. Semantic match against VALID regulations, re-ranked against
        #    each candidate's typed numeric thresholds (cap/floor/exact).
        val_similarity, conflict, val_meta = _best_valid_candidate(
            claim, valid_hits["metadatas"][i], valid_hits["distances"][i], known_percent=known_percent
        )
        closest_rule = val_meta["title"]

        if conflict is not None:
            has_hallucination = True
            relation = {"cap": "no more than", "floor": "at least", "exact": "exactly"}[conflict["expected_type"]]
            unsupported_claims.append({
                "claim": f"{claim} (NUMERIC MISMATCH)",
                "closest_rule": closest_rule,
                "why_false": (
                    f"Claims {conflict['claimed_value']}{conflict['unit']} but {closest_rule} "
                    f"requires {relation} {conflict['expected_value']}{conflict['unit']}."
                ),
                "score": 0.0
            })
            total_grounding += 0.0
            continue

        claim_score = _claim_score(val_similarity)
        total_grounding += claim_score

        if claim_score < 0.50:
            has_hallucination = True
            unsupported_claims.append({
                "claim": f"{claim} (COMPLETELY FALSE - Invented claim)",
                "closest_rule": "No relevant RBI/SEBI guideline found.",
                "score": val_similarity
            })
        elif claim_score < 1.0:
            unsupported_claims.append({
                "claim": claim,
                "closest_rule": closest_rule,
                "score": val_similarity,
                "source": val_meta["source"],
                "citation": val_meta.get("citation", ""),
                "url": val_meta.get("url", ""),
            })

    # Averaged Metrics
    avg_grounding_score = total_grounding / len(claims)
    is_grounded = avg_grounding_score > 0.75 and not has_hallucination

    return {
        "grounded": is_grounded,
        "hallucination": has_hallucination,
        "grounding_score": round(avg_grounding_score, 4),
        "unsupported_claims": unsupported_claims
    }
