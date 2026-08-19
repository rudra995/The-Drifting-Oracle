# The Drifting Oracle

A credit-risk default-prediction system that watches for when the world stops looking like its training data, hands off to a standby model and retrains itself when that happens — paired with an LLM explanation layer that's independently fact-checked against real regulations, so it can't confidently cite a rule that doesn't exist.

Built for a hackathon, then hardened phase by phase into a portfolio piece: real MLOps (Databricks + MLflow + Unity Catalog), containerized + orchestrated (Docker + Kubernetes + Prefect), and a GenAI/agentic layer (LangGraph + a local RAG auditor over ChromaDB). Every claim in this README is backed by a real, passing test or a live-verified run — see `docs/interview-prep.pdf` for the full write-up, including known limitations stated up front.

## Architecture

```mermaid
flowchart TD
    U[CSV Upload / Single Prediction] --> API[FastAPI backend]
    API --> PSI[PSI drift check<br/>vs. training baseline]
    PSI -->|PSI < 0.25| CH[Champion model<br/>XGBoost, 20 features]
    PSI -->|PSI ≥ 0.25| CL[Challenger model<br/>XGBoost, 8-feature schema]
    PSI -->|drift detected| RETRAIN[Prefect retrain flow]
    RETRAIN --> GROW[continual_retrain.py<br/>grows the training corpus]
    RETRAIN --> RELOAD[Hot-reload into server]
    CH --> GRAPH[LangGraph: explain → evaluate]
    CL --> GRAPH
    GRAPH --> LLM[Llama (Ollama) → Gemini fallback]
    LLM --> RAG[ChromaDB RAG auditor<br/>+ numeric threshold check]
    RAG -->|hallucination flagged, 1 retry| GRAPH
    RAG --> RESP[JSON response]
    API -.fire-and-forget.-> DELTA[(Databricks Delta Lake<br/>4 governed tables)]
    RETRAIN -.-> MLFLOW[(MLflow + Unity Catalog<br/>Champion/Challenger registry)]
```

## What it actually does

1. **Drift-aware serving** — every batch is compared against the training distribution via [PSI (Population Stability Index)](https://en.wikipedia.org/wiki/Population_stability_index) across 7 features. Below the industry-standard 0.25 threshold, the Champion model serves traffic; at or above it, a differently-built Challenger model takes over and a real Prefect flow retrains both models in the background.
2. **Growing-window continual learning** — a real drifted batch has no ground-truth labels (the label-lag problem), so instead of silently ignoring that or pretending otherwise, `continual_retrain.py` resamples real labeled historical rows, shifts their features to match the observed drift, and appends them to a persisted, growing training corpus — proven first via a standalone harness (`scripts/continual_learning_demo.py`) that measurably recovers AUC after each simulated drift event.
3. **A hallucination-audited LLM explainer** — every prediction gets a plain-English explanation from a local Llama model (Ollama) with a Gemini fallback, modeled as an explicit LangGraph state graph (`predict → explain → evaluate`, with one capped retry on a flagged hallucination). Every claim is checked against a local ChromaDB store of real RBI/SEBI regulations, plus a typed numeric-threshold layer that catches "right topic, wrong number" claims embedding similarity alone would miss.
4. **Full governance trail** — every prediction, drift event, LLM evaluation, and retrain decision is logged to Databricks Delta Lake (fire-and-forget, never blocks the live API) and surfaced on a Governance page in the frontend.

## Project structure

```
The-Drifting-Oracle/
├── backend/
│   ├── main.py               # FastAPI app, all routes, lifespan startup
│   ├── config.py             # constants, shared state, auth
│   ├── psi.py                # PSI drift detection
│   ├── preprocessing.py      # feature engineering (Champion + Challenger)
│   ├── model_loader.py       # model/feature loading
│   ├── retrain.py            # Prefect-orchestrated drift-triggered retrain
│   ├── continual_retrain.py  # growing-window training corpus
│   ├── llm_graph.py          # LangGraph predict→explain→evaluate
│   ├── llm_evaluator.py      # ChromaDB RAG hallucination auditor
│   ├── llm_explanation.py    # Llama → Gemini fallback chain
│   ├── databricks_io.py      # async Delta Lake writes
│   ├── scripts/              # train.py, tune_threshold.py, setup scripts, demos
│   └── tests/                # pytest suite (79 tests)
├── frontend/                 # React (Vite) — 8 routed pages
│   └── src/
│       ├── api.js            # centralized fetch wrapper (API_BASE, auth header)
│       ├── pages/             # Dashboard, Upload, Drift, Governance, Model Training, LLM Eval, Settings, Profile
│       └── components/
├── k8s/                      # Deployment/Service manifests, secret template
├── docker-compose.yml        # local multi-container dev
├── docs/interview-prep.pdf   # full project write-up (architecture, decisions, Q&A)
└── screenshots/              # of every frontend page
```

## Getting started

### Prerequisites
- Python 3.12, Node.js 18+
- A Kaggle account (for `dataset/raw/application_train.csv` — see `backend/dataset/`) if you want to retrain from scratch
- Optional, for full functionality: a Databricks workspace (MLflow/Unity Catalog/Delta Lake), a Gemini API key, and Ollama running locally

### Backend
```bash
cd backend
python -m venv venv && venv\Scripts\activate      # or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env                                # fill in what you have; everything is optional-by-default
uvicorn main:app --reload
```
API at `http://localhost:8000`, docs at `/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App at `http://localhost:5173`.

### Docker Compose (both services)
```bash
docker compose up --build
```

### Kubernetes
See `k8s/README.md` — copy `k8s/backend-secret.example.yaml` to `backend-secret.yaml`, fill it in, then `kubectl apply -f k8s/`.

## API endpoints

| Method | Endpoint                    | Description                                      |
| ------ | ---------------------------- | ------------------------------------------------- |
| GET    | `/api/health`                | Health check (K8s liveness/readiness probe)        |
| POST   | `/predict`                   | Single-row prediction (always Champion; PSI is meaningless at n=1) |
| POST   | `/predict_batch`             | Batch prediction — the core pipeline (PSI → model select → predict → explain → audit) |
| GET    | `/psi`                       | Currently configured PSI features/threshold        |
| POST   | `/fill_window`                | Demo endpoint: sample synthetic drift for testing  |
| GET    | `/api/v1/dashboard-metrics`  | KPI summary for the Dashboard page                 |
| GET    | `/api/v1/drift-history`       | Recent PSI/drift events                             |
| GET    | `/api/v1/models`              | Champion/Challenger registry status + metrics       |
| GET    | `/api/v1/llm-evaluations`     | Recent hallucination/grounding audit results        |
| GET    | `/api/v1/governance-log`      | Full audit trail                                     |

All routes except `/` and `/api/health` are gated behind an optional `X-API-Key` header — see `config.API_KEY` (unset by default; every route stays open until you configure one).

## Testing

```bash
cd backend
pytest tests/ -v
```
79 tests: PSI math and edge cases, feature engineering for both model schemas, the LLM fallback chain, the LangGraph retry logic, the RAG grounding checker, the growing-window corpus mechanics, the auth gate, and FastAPI endpoint integration via `TestClient`. GitHub Actions runs this (plus frontend eslint/build) on every push.

## Key design decisions

- **PSI over KL-divergence** — symmetric, bounded into bands (`<0.10` / `0.10–0.25` / `≥0.25`) a credit-risk team already has intuition for.
- **Champion/Challenger over a single self-retraining model** — a fresh retrain is never blindly trusted with zero live scrutiny; drift explicitly hands off to a differently-built standby instead.
- **ChromaDB over Pinecone** — the regulation corpus is 21 entries; a hosted vector database with quotas would solve a scale problem this project doesn't have, and would break a deliberate zero-cost constraint. Same RAG pattern, self-hosted.
- **No Claude fallback in the LLM chain** — Anthropic's API has no standing free tier, which doesn't fit this project's zero-cost constraint everywhere else.
- **Retraining is a real, scoped mechanism** — drift-triggered retrain grows a real persisted corpus (`continual_retrain.py`), but since a live drifted batch has no ground-truth labels, that growth is a disclosed, calibrated proxy — not a claim of learning from real new outcomes.

Full rationale, trade-offs, and known limitations (stated proactively, not hidden) are in `docs/interview-prep.pdf`.

## Status

Phases 0–6 of the hardening roadmap are complete: security/hygiene, Delta Lake persistence, real MLOps (Databricks/MLflow/Unity Catalog), CI + a real pytest suite, containerization + Kubernetes + Prefect orchestration, the LangGraph/RAG GenAI layer, and product-correctness fixes (auth gate, error handling, growing-window retraining wired into the live path). This README and the architecture diagram above are the last item on that list.
