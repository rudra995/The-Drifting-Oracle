import os
import re

# Redirect HF model cache to D: drive (C: may not have enough space for model weights)
os.environ.setdefault("HF_HOME", r"D:\hackbricks\hf_cache")

import torch
from sentence_transformers import SentenceTransformer, util

# ----------------------------------------------------
# STEP 1: RBI RULE BASE
# ----------------------------------------------------
# Extracted from rbi_sebi_ground_truth.md section 5.1
valid_regulations = [
    "Disbursement must be directly into borrower's bank account",
    "All borrower data must be stored in India; if processed abroad, must be deleted within 24 hours",
    "30-day cooling-off period before reassessing rejected loan applications",
    "Risk weight on unsecured personal loans increased to 125% or higher based on internal assessment",
    "DLG cover limited to maximum 5% of total disbursed amount of specified loan portfolio",
    "Enhanced KYC requiring bank statements, ITRs, and employment verification",
    "Originating lender may provide DLG of up to 5% of loan amount",
    "Banks must assess repayment capacity before loan approval",
    "High debt-to-income ratio indicates higher default risk",
    "Systemic risk is managed by refusing loans with predicted default risk exceeding 0.5"
]

# Extracted from rbi_sebi_ground_truth.md section 5.2
invalid_regulations = [
    {
        "claim": "RBI mandates immediate rejection of all applications from borrowers with income below 2 lakhs per annum",
        "true_rule": "Risk-based pricing and underwriting required; no blanket income limits"
    },
    {
        "claim": "RBI Circular 2024-11 mandates notarized documents for all loan applicants",
        "true_rule": "Digital KYC and digitally signed documents via email/SMS permitted"
    },
    {
        "claim": "Section 42(A) of the RBI Act prohibits lending to self-employed without 5 years of tax returns",
        "true_rule": "Enhanced verification required; specific requirements vary by lender policy"
    },
    {
        "claim": "SEBI prohibits NBFCs from offering personal loans below 12% interest rate",
        "true_rule": "NBFC interest rates deregulated; determined by Board policy"
    },
    {
        "claim": "Cooling-off period for rejected applications is 60 days per RBI 2025 guidelines",
        "true_rule": "30-day cooling-off period before reassessing rejected loan applications"
    },
    {
        "claim": "RBI mandates all loans above 5 lakhs require government-backed collateral",
        "true_rule": "Risk-weighting varies; collateral not mandated for personal loans"
    }
]
invalid_sentences = [x["claim"] for x in invalid_regulations]

# ----------------------------------------------------
# STEP 2 & 3: EMBEDDING MODEL & PRECOMPUTING
# ----------------------------------------------------
print("[LLM Evaluator] Loading sentence-transformers model (all-MiniLM-L6-v2) with strict RBI ground truth...")
try:
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    valid_embeddings = embedding_model.encode(valid_regulations, convert_to_tensor=True)
    invalid_embeddings = embedding_model.encode(invalid_sentences, convert_to_tensor=True)
    print("[LLM Evaluator] Successfully loaded ground truth embeddings.")
except Exception as e:
    print(f"[LLM Evaluator] Warning: Failed to load embedding model. {e}")
    embedding_model = None
    valid_embeddings = None
    invalid_embeddings = None

# ----------------------------------------------------
# STEP 4, 5, 6, 7: CLAIM EXTRACTION & VERIFICATION
# ----------------------------------------------------
def evaluate_explanation(explanation: str) -> dict:
    if embedding_model is None or valid_embeddings is None:
        return {
            "grounded": False,
            "hallucination": False,
            "grounding_score": 0.0,
            "unsupported_claims": [{"claim": "System Error: Evaluator model not loaded", "score": 0.0}]
        }

    raw_sentences = re.split(r'[\.\!\?\n]+', explanation)
    claims = [s.strip() for s in raw_sentences if len(s.strip()) > 10]

    if not claims:
        return {
            "grounded": False,
            "hallucination": True,
            "grounding_score": 0.0,
            "unsupported_claims": [{"claim": "No meaningful claims extracted.", "score": 0.0}]
        }

    claim_embeddings = embedding_model.encode(claims, convert_to_tensor=True)
    
    val_cos_scores = util.cos_sim(claim_embeddings, valid_embeddings)
    inv_cos_scores = util.cos_sim(claim_embeddings, invalid_embeddings)

    unsupported_claims = []
    total_grounding = 0.0
    has_hallucination = False

    for i, claim in enumerate(claims):
        # 1. Exact/Semantic match against KNOWN INVALID regulations
        best_inv_score = float(torch.max(inv_cos_scores[i]).item())
        if best_inv_score > 0.75:
            # Matches a known hallucination factually
            best_inv_idx = int(torch.argmax(inv_cos_scores[i]).item())
            inv_rule = invalid_regulations[best_inv_idx]
            
            has_hallucination = True
            unsupported_claims.append({
                "claim": f"{claim} (KNOWN HALLUCINATION FLAG)",
                "closest_rule": inv_rule["true_rule"],
                "score": 0.0
            })
            continue

        # 2. Semantic match against VALID regulations
        best_val_score = float(torch.max(val_cos_scores[i]).item())
        best_val_idx = int(torch.argmax(val_cos_scores[i]).item())
        closest_rule = valid_regulations[best_val_idx]
        
        # Scoring logic mapped to Section 4.1 Factual Grounding Score
        if best_val_score >= 0.80:
            claim_score = 1.0     # Exact/Strong match
        elif best_val_score >= 0.65:
            claim_score = 0.75    # Correct concept / partial
        elif best_val_score >= 0.50:
            claim_score = 0.50    # Partially correct / misapplied
        elif best_val_score >= 0.35:
            claim_score = 0.25    # Related but factually inaccurate
        else:
            claim_score = 0.0     # Complete hallucination
            
        total_grounding += claim_score

        if claim_score < 0.50:
            has_hallucination = True
            unsupported_claims.append({
                "claim": f"{claim} (COMPLETELY FALSE - Invented claim)",
                "closest_rule": "No relevant RBI guideline found.",
                "score": best_val_score
            })
        elif claim_score < 1.0:
            # Uncertain / Unsupported but somewhat related
            unsupported_claims.append({
                "claim": claim,
                "closest_rule": closest_rule,
                "score": best_val_score
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
