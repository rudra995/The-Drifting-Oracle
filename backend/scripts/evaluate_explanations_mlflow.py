"""
LLM Explanation Evaluation Pipeline -- MLflow custom metrics
================================================================

Pulls the loan-rejection explanations already logged in Delta
(drifting_oracle.monitoring.llm_evaluations, written in real time by
config.log_llm_evaluation for every /predict and /predict_batch call)
and runs them through two custom metrics -- factual grounding and
hallucination detection -- logging the results as a proper MLflow run:
aggregate metrics, a per-row results table, and a JSON artifact of any
flagged hallucinations.

This is the "mlflow.evaluate() with custom metrics" pipeline from the
original brief, built on plain MLflow primitives (log_metrics,
log_table) instead of the evaluate()/genai.evaluate() orchestrators --
both were tried here and reproducibly hung (0% CPU, indefinitely) in
this environment; see scripts/train.py's log_and_evaluate() docstring
for the classifier-evaluate() case. Same failure mode, same fix: score
directly, log the numbers straight to MLflow, skip the flaky wrapper.

Usage:
    python scripts/evaluate_explanations_mlflow.py [--limit 100]
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("MPLBACKEND", "Agg")

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd
import requests
import mlflow
from dotenv import load_dotenv

load_dotenv()

from llm_evaluator import evaluate_explanation

HOST = os.getenv("DATABRICKS_HOST", "").rstrip("/")
TOKEN = os.getenv("DATABRICKS_TOKEN", "")
WAREHOUSE_ID = os.getenv("DATABRICKS_HTTP_PATH", "").rstrip("/").split("/")[-1]
CATALOG = os.getenv("DATABRICKS_CATALOG", "drifting_oracle")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "monitoring")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
EXPERIMENT_PATH = "/Users/solankirudra66@gmail.com/drifting-oracle"


def query_delta(sql: str, timeout_s: int = 60) -> pd.DataFrame:
    """Minimal synchronous query helper against the SQL Statement Execution API."""
    resp = requests.post(
        f"{HOST}/api/2.0/sql/statements",
        headers=HEADERS,
        json={"statement": sql, "warehouse_id": WAREHOUSE_ID, "wait_timeout": "30s"},
        timeout=40,
    )
    resp.raise_for_status()
    result = resp.json()
    statement_id = result["statement_id"]
    state = result["status"]["state"]

    start = time.time()
    while state in ("PENDING", "RUNNING"):
        if time.time() - start > timeout_s:
            raise TimeoutError("Delta query timed out")
        time.sleep(2)
        result = requests.get(
            f"{HOST}/api/2.0/sql/statements/{statement_id}", headers=HEADERS, timeout=20
        ).json()
        state = result["status"]["state"]

    if state != "SUCCEEDED":
        raise RuntimeError(f"Delta query failed [{state}]: {result['status'].get('error')}")

    cols = [c["name"] for c in result["manifest"]["schema"]["columns"]]
    rows = result.get("result", {}).get("data_array", [])
    return pd.DataFrame(rows, columns=cols)


def score_explanation(explanation: str) -> dict:
    """Two custom metrics, both derived from the existing embedding-based checker:
    factual grounding (0-1, higher is better) and hallucination (bool)."""
    result = evaluate_explanation(explanation)
    return {
        "factual_grounding_score": result["grounding_score"],
        "hallucination_detected": result["hallucination"],
        "unsupported_claim_count": len(result.get("unsupported_claims", [])),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    print(f"[eval] Pulling up to {args.limit} explanations from "
          f"{CATALOG}.{SCHEMA}.llm_evaluations ...")
    df = query_delta(
        f"SELECT eval_id, event_timestamp, explanation, llm_used "
        f"FROM `{CATALOG}`.`{SCHEMA}`.llm_evaluations "
        f"ORDER BY event_timestamp DESC LIMIT {args.limit}"
    )
    print(f"[eval]   {len(df)} rows pulled")

    if df.empty:
        print("[eval] No explanations logged yet -- run some /predict or /predict_batch "
              "calls first, then re-run this script.")
        return

    scores = df["explanation"].apply(score_explanation)
    scored = pd.concat([df, pd.DataFrame(list(scores))], axis=1)

    agg_metrics = {
        "n_explanations": len(scored),
        "mean_grounding_score": round(scored["factual_grounding_score"].mean(), 4),
        "hallucination_rate": round(scored["hallucination_detected"].mean(), 4),
        "mean_unsupported_claims": round(scored["unsupported_claim_count"].mean(), 4),
    }

    mlflow.set_tracking_uri("databricks")
    mlflow.set_experiment(EXPERIMENT_PATH)

    with mlflow.start_run(run_name="llm-explanation-eval"):
        mlflow.log_metrics({
            "mean_grounding_score": agg_metrics["mean_grounding_score"],
            "hallucination_rate": agg_metrics["hallucination_rate"],
            "mean_unsupported_claims": agg_metrics["mean_unsupported_claims"],
        })
        mlflow.log_param("n_explanations", agg_metrics["n_explanations"])
        mlflow.log_table(
            data=scored[["eval_id", "llm_used", "factual_grounding_score",
                          "hallucination_detected", "unsupported_claim_count", "explanation"]],
            artifact_file="explanation_scores.json",
        )

        flagged = scored[scored["hallucination_detected"]]
        mlflow.log_dict(
            json.loads(flagged[["eval_id", "explanation"]].to_json(orient="records")),
            "flagged_hallucinations.json",
        )

        run_id = mlflow.active_run().info.run_id

    print(f"[eval] Logged run {run_id}")
    print(f"[eval] Summary: {agg_metrics}")

    import databricks_io
    databricks_io.insert_governance_event(
        "LLM_EVAL_PIPELINE_RUN",
        (
            f"Scored {agg_metrics['n_explanations']} explanations from llm_evaluations. "
            f"Mean grounding={agg_metrics['mean_grounding_score']}, "
            f"hallucination_rate={agg_metrics['hallucination_rate']}. "
            f"MLflow run: {run_id}"
        ),
        "llm-eval-pipeline",
    )


if __name__ == "__main__":
    main()
