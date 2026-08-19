"""
ChromaDB Setup -- The Drifting Oracle
========================================

Builds the local, persistent ChromaDB vector store used by llm_evaluator.py
for RAG-based grounding/hallucination checks (Phase 5 of the remediation
roadmap), replacing the old fixed 16-item in-memory regulation list.

Two collections, both embedded with the same all-MiniLM-L6-v2 model already
used elsewhere in the project:
  - rbi_valid_regulations   -- real, sourced RBI/SEBI regulations
  - rbi_invalid_regulations -- known-fabricated claims, for exact/near
                                hallucination matching

Rebuilds from scratch every run (drop + recreate) -- the corpus is tiny
(~20 short entries), so a full rebuild costs milliseconds and this avoids
any risk of stale entries surviving a corpus edit. Safe to re-run.

Also importable: llm_evaluator.py calls ensure_collections() at startup so
the store is built automatically on first run, with no manual step needed.

Usage:
    python scripts/setup_chromadb.py
"""
import json
import os

import chromadb

CORPUS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "rbi_regulations_corpus.json")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")

VALID_COLLECTION = "rbi_valid_regulations"
INVALID_COLLECTION = "rbi_invalid_regulations"


def _load_corpus() -> dict:
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _embedding_function():
    # Imported lazily -- sentence-transformers/torch are heavy and this
    # module may be imported by scripts that don't need embedding at all.
    from chromadb.utils import embedding_functions
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


def build_collections(client: "chromadb.ClientAPI" = None) -> tuple:
    """(Re)build both collections from the corpus JSON. Returns (valid_collection, invalid_collection)."""
    if client is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)

    corpus = _load_corpus()
    ef = _embedding_function()

    for name in (VALID_COLLECTION, INVALID_COLLECTION):
        try:
            client.delete_collection(name)
        except Exception:
            pass  # doesn't exist yet -- fine

    # Explicit cosine space -- Chroma defaults to squared L2, but
    # llm_evaluator.py's grounding thresholds assume cosine similarity
    # (1 - cosine distance), matching the original cos_sim-based design.
    valid_coll = client.create_collection(VALID_COLLECTION, embedding_function=ef, metadata={"hnsw:space": "cosine"})
    invalid_coll = client.create_collection(INVALID_COLLECTION, embedding_function=ef, metadata={"hnsw:space": "cosine"})

    valid_regs = corpus["valid_regulations"]
    valid_coll.add(
        ids=[r["id"] for r in valid_regs],
        documents=[r["rule"] for r in valid_regs],
        metadatas=[
            {
                "title": r["title"],
                "category": r["category"],
                "source": r["source"],
                "citation": r.get("citation", ""),
                "url": r.get("url", ""),
                "confidence": r["confidence"],
                # Chroma metadata values must be scalar -- numeric thresholds
                # (with cap/floor/exact type) are JSON-encoded and decoded
                # back in llm_evaluator.py's numeric conflict check.
                "thresholds_json": json.dumps(r.get("thresholds", [])),
            }
            for r in valid_regs
        ],
    )

    invalid_regs = corpus["invalid_regulations"]
    invalid_coll.add(
        ids=[r["id"] for r in invalid_regs],
        documents=[r["claim"] for r in invalid_regs],
        metadatas=[
            {
                "why_false": r["why_false"],
                "true_rule": r["true_rule"],
                "true_rule_id": r["true_rule_id"],
            }
            for r in invalid_regs
        ],
    )

    print(f"[setup_chromadb] Loaded {len(valid_regs)} valid regulations, {len(invalid_regs)} invalid/fabricated examples into {CHROMA_DIR}")
    return valid_coll, invalid_coll


def ensure_collections() -> tuple:
    """Return (valid_collection, invalid_collection), building them if the store is missing or empty."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = _embedding_function()
    try:
        valid_coll = client.get_collection(VALID_COLLECTION, embedding_function=ef)
        invalid_coll = client.get_collection(INVALID_COLLECTION, embedding_function=ef)
        if valid_coll.count() > 0 and invalid_coll.count() > 0:
            return valid_coll, invalid_coll
    except Exception:
        pass
    return build_collections(client)


if __name__ == "__main__":
    build_collections()
