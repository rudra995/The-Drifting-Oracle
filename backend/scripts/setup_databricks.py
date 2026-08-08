"""
Databricks Schema Setup — The Drifting Oracle
===============================================

Idempotent DDL: creates the Unity Catalog catalog, schema, and the four
governed Delta tables that back drift/governance/eval monitoring
(Phase 1 of the remediation roadmap).

Safe to re-run — every statement is IF NOT EXISTS.

Usage:
    python scripts/setup_databricks.py
"""
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("DATABRICKS_HOST", "").rstrip("/")
TOKEN = os.getenv("DATABRICKS_TOKEN", "")
HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
CATALOG = os.getenv("DATABRICKS_CATALOG", "drifting_oracle")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "monitoring")

# Extract warehouse_id from the http_path, e.g. /sql/1.0/warehouses/<id>
WAREHOUSE_ID = HTTP_PATH.rstrip("/").split("/")[-1] if HTTP_PATH else ""

STATEMENTS_ENDPOINT = f"{HOST}/api/2.0/sql/statements"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def run_statement(sql: str, timeout_s: int = 120) -> None:
    """Submit a SQL statement to the warehouse and poll until it finishes."""
    payload = {
        "statement": sql,
        "warehouse_id": WAREHOUSE_ID,
        "wait_timeout": "30s",  # max the API allows synchronously
    }
    resp = requests.post(STATEMENTS_ENDPOINT, headers=HEADERS, json=payload, timeout=40)
    resp.raise_for_status()
    result = resp.json()

    statement_id = result["statement_id"]
    state = result["status"]["state"]

    start = time.time()
    while state in ("PENDING", "RUNNING"):
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Statement did not finish within {timeout_s}s: {sql[:80]}")
        time.sleep(3)
        poll = requests.get(f"{STATEMENTS_ENDPOINT}/{statement_id}", headers=HEADERS, timeout=20)
        poll.raise_for_status()
        result = poll.json()
        state = result["status"]["state"]
        print(f"  ... {state} ({int(time.time() - start)}s elapsed, warehouse may be waking up)")

    if state != "SUCCEEDED":
        error = result["status"].get("error", {})
        raise RuntimeError(f"Statement failed [{state}]: {error.get('message', result)}")


DDL_STATEMENTS = [
    (f"Create catalog `{CATALOG}`", f"CREATE CATALOG IF NOT EXISTS `{CATALOG}`"),
    (f"Create schema `{CATALOG}.{SCHEMA}`", f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`"),
    (
        "Create table governance_log",
        f"""
        CREATE TABLE IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.governance_log (
            event_id STRING,
            event_timestamp TIMESTAMP,
            event_type STRING,
            details STRING,
            model_id STRING
        ) USING DELTA
        COMMENT 'Audit trail of system events: model loads, drift alerts, batch predictions, retraining.'
        """,
    ),
    (
        "Create table drift_events",
        f"""
        CREATE TABLE IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.drift_events (
            event_id STRING,
            event_timestamp TIMESTAMP,
            overall_psi DOUBLE,
            drift_detected BOOLEAN,
            drift_features_json STRING,
            recommendation STRING
        ) USING DELTA
        COMMENT 'PSI drift detection results per scored batch, one row per batch.'
        """,
    ),
    (
        "Create table llm_evaluations",
        f"""
        CREATE TABLE IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.llm_evaluations (
            eval_id STRING,
            event_timestamp TIMESTAMP,
            explanation STRING,
            llm_used STRING,
            factual_grounding_score DOUBLE,
            hallucination_score DOUBLE,
            status STRING,
            issues_found_json STRING
        ) USING DELTA
        COMMENT 'Hallucination/grounding audit results for every LLM-generated explanation.'
        """,
    ),
    (
        "Create table predictions",
        f"""
        CREATE TABLE IF NOT EXISTS `{CATALOG}`.`{SCHEMA}`.predictions (
            batch_id STRING,
            event_timestamp TIMESTAMP,
            total_rows INT,
            avg_probability DOUBLE,
            default_rate DOUBLE,
            model_used STRING,
            overall_psi DOUBLE,
            drift_detected BOOLEAN,
            decision STRING
        ) USING DELTA
        COMMENT 'One row per /predict or /predict_batch call: model routing decision + outcome summary.'
        """,
    ),
]


def main():
    if not (HOST and TOKEN and WAREHOUSE_ID):
        print("Missing DATABRICKS_HOST / DATABRICKS_TOKEN / DATABRICKS_HTTP_PATH in .env")
        sys.exit(1)

    print(f"Target: {CATALOG}.{SCHEMA} @ {HOST} (warehouse {WAREHOUSE_ID})\n")

    for label, sql in DDL_STATEMENTS:
        print(f"[{label}]")
        t0 = time.time()
        run_statement(sql)
        print(f"  done in {time.time() - t0:.1f}s\n")

    print("All catalog/schema/tables ready.")


if __name__ == "__main__":
    main()
