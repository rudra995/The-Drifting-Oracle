"""
Databricks Delta Lake I/O
==========================

Writes monitoring events (governance, drift, LLM evaluations, predictions)
to governed Unity Catalog Delta tables via the SQL Statement Execution API.

Design:
  - Every write is fire-and-forget from a small background thread pool so a
    slow/cold warehouse never blocks the request/response path.
  - Failures are logged and swallowed -- Databricks is a durability and
    governance sink here, not the source of truth for the live dashboard.
    config.py's in-memory lists still serve reads, same as before.
"""
import os
import time
import uuid
import json
import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("databricks_io")

HOST = os.getenv("DATABRICKS_HOST", "").rstrip("/")
TOKEN = os.getenv("DATABRICKS_TOKEN", "")
HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
CATALOG = os.getenv("DATABRICKS_CATALOG", "drifting_oracle")
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "monitoring")
WAREHOUSE_ID = HTTP_PATH.rstrip("/").split("/")[-1] if HTTP_PATH else ""

STATEMENTS_ENDPOINT = f"{HOST}/api/2.0/sql/statements" if HOST else ""
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

ENABLED = bool(HOST and TOKEN and WAREHOUSE_ID)
if not ENABLED:
    logger.warning(
        "[databricks_io] Disabled -- DATABRICKS_HOST/TOKEN/HTTP_PATH not fully set. "
        "Monitoring writes will be skipped (dashboard still works from in-memory cache)."
    )

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="databricks-io")


def _run_statement(sql: str, parameters: list[dict], timeout_s: int = 60) -> None:
    payload = {
        "statement": sql,
        "warehouse_id": WAREHOUSE_ID,
        "wait_timeout": "30s",
        "parameters": parameters,
    }
    resp = requests.post(STATEMENTS_ENDPOINT, headers=HEADERS, json=payload, timeout=40)
    resp.raise_for_status()
    result = resp.json()

    statement_id = result["statement_id"]
    state = result["status"]["state"]

    start = time.time()
    while state in ("PENDING", "RUNNING"):
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Databricks statement timed out after {timeout_s}s")
        time.sleep(2)
        poll = requests.get(f"{STATEMENTS_ENDPOINT}/{statement_id}", headers=HEADERS, timeout=20)
        poll.raise_for_status()
        result = poll.json()
        state = result["status"]["state"]

    if state != "SUCCEEDED":
        error = result["status"].get("error", {})
        raise RuntimeError(f"Databricks statement failed [{state}]: {error.get('message', result)}")


def _fire_and_forget(sql: str, parameters: list[dict]) -> None:
    """Submit a write on a background thread. Never raises into the caller."""
    if not ENABLED:
        return

    def _task():
        try:
            _run_statement(sql, parameters)
        except Exception as e:
            logger.warning(f"[databricks_io] write failed (non-fatal, in-memory log still has it): {e}")

    _executor.submit(_task)


def _param(name: str, value, type_: str = "STRING") -> dict:
    return {"name": name, "value": None if value is None else str(value), "type": type_}


# --------------------------------------------------------------------
# Table writers -- one per governed Delta table
# --------------------------------------------------------------------

def insert_governance_event(event_type: str, details: str, model_id: str | None) -> None:
    sql = f"""
        INSERT INTO `{CATALOG}`.`{SCHEMA}`.governance_log
        (event_id, event_timestamp, event_type, details, model_id)
        VALUES (:event_id, current_timestamp(), :event_type, :details, :model_id)
    """
    _fire_and_forget(sql, [
        _param("event_id", str(uuid.uuid4())),
        _param("event_type", event_type),
        _param("details", details),
        _param("model_id", model_id),
    ])


def insert_drift_event(overall_psi: float, per_feature: dict, drift_detected: bool, recommendation: str) -> None:
    sql = f"""
        INSERT INTO `{CATALOG}`.`{SCHEMA}`.drift_events
        (event_id, event_timestamp, overall_psi, drift_detected, drift_features_json, recommendation)
        VALUES (:event_id, current_timestamp(), :overall_psi, :drift_detected, :features_json, :recommendation)
    """
    _fire_and_forget(sql, [
        _param("event_id", str(uuid.uuid4())),
        _param("overall_psi", overall_psi, "DOUBLE"),
        _param("drift_detected", str(bool(drift_detected)).lower(), "BOOLEAN"),
        _param("features_json", json.dumps(per_feature)),
        _param("recommendation", recommendation),
    ])


def insert_llm_evaluation(explanation: str, llm_used: str, factual_grounding_score: float,
                           hallucination_score: float, status: str, issues_found: list) -> None:
    sql = f"""
        INSERT INTO `{CATALOG}`.`{SCHEMA}`.llm_evaluations
        (eval_id, event_timestamp, explanation, llm_used, factual_grounding_score,
         hallucination_score, status, issues_found_json)
        VALUES (:eval_id, current_timestamp(), :explanation, :llm_used, :grounding,
                :hallucination, :status, :issues_json)
    """
    _fire_and_forget(sql, [
        _param("eval_id", str(uuid.uuid4())),
        _param("explanation", explanation),
        _param("llm_used", llm_used),
        _param("grounding", factual_grounding_score, "DOUBLE"),
        _param("hallucination", hallucination_score, "DOUBLE"),
        _param("status", status),
        _param("issues_json", json.dumps(issues_found, default=str)),
    ])


def insert_prediction(total_rows: int, avg_probability: float, default_rate: float,
                       model_used: str, overall_psi: float, drift_detected: bool, decision: str) -> None:
    sql = f"""
        INSERT INTO `{CATALOG}`.`{SCHEMA}`.predictions
        (batch_id, event_timestamp, total_rows, avg_probability, default_rate,
         model_used, overall_psi, drift_detected, decision)
        VALUES (:batch_id, current_timestamp(), :total_rows, :avg_prob, :default_rate,
                :model_used, :psi, :drift_detected, :decision)
    """
    _fire_and_forget(sql, [
        _param("batch_id", str(uuid.uuid4())),
        _param("total_rows", total_rows, "INT"),
        _param("avg_prob", avg_probability, "DOUBLE"),
        _param("default_rate", default_rate, "DOUBLE"),
        _param("model_used", model_used),
        _param("psi", overall_psi, "DOUBLE"),
        _param("drift_detected", str(bool(drift_detected)).lower(), "BOOLEAN"),
        _param("decision", decision),
    ])
