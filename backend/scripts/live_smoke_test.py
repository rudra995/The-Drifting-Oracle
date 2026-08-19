"""
Live smoke test against a running backend (http://localhost:8000).
Exercises every endpoint with real requests and real data, prints a
pass/fail summary. Not a pytest suite -- a human-readable real-world check.
"""
import json
import sys
import time

import requests

BASE = "http://localhost:8000"
RESULTS = []


def check(name, fn):
    try:
        ok, detail = fn()
        RESULTS.append((name, ok, detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {name} -- {detail}")
    except Exception as e:
        RESULTS.append((name, False, f"EXCEPTION: {e}"))
        print(f"[FAIL] {name} -- EXCEPTION: {e}")


def t_health():
    r = requests.get(f"{BASE}/api/health", timeout=10)
    d = r.json()
    return r.status_code == 200 and d.get("model_loaded") and d.get("baseline_loaded"), json.dumps(d)


def t_psi():
    r = requests.get(f"{BASE}/psi", timeout=10)
    d = r.json()
    return r.status_code == 200 and d.get("baseline_loaded"), json.dumps(d)


def t_predict_single():
    payload = {
        "AMT_INCOME_TOTAL": 202500.0, "AMT_CREDIT_x": 406597.5, "AMT_ANNUITY": 24700.5,
        "CNT_CHILDREN": 0, "CNT_FAM_MEMBERS": 1, "DAYS_EMPLOYED": -637,
        "EXT_SOURCE_1": 0.083, "EXT_SOURCE_2": 0.263, "EXT_SOURCE_3": 0.139,
        "REGION_POPULATION_RELATIVE": 0.0188, "REGION_RATING_CLIENT": 2,
        "FLAG_EMP_PHONE": 1, "FLAG_WORK_PHONE": 0, "age": 46.2,
        "income_credit_ratio": 0.498, "annuity_ratio": 0.061,
        "CODE_GENDER_M": 1, "CODE_GENDER_XNA": 0, "FLAG_OWN_CAR_Y": 0, "FLAG_OWN_REALTY_Y": 1,
    }
    r = requests.post(f"{BASE}/predict", json=payload, timeout=60)
    d = r.json()
    # /predict's real response shape: "explanation" is top-level (not
    # nested under llm_evaluation, which holds the grounding/hallucination
    # check result instead), and the LLM name is "explanation_llm".
    ok = r.status_code == 200 and "probability" in d and "explanation" in d
    return ok, f"status={d.get('risk_label')} prob={d.get('probability')} llm_used={d.get('explanation_llm')}"


def t_predict_batch(csv_path, label):
    with open(csv_path, "rb") as f:
        files = {"file": (csv_path.split("/")[-1], f, "text/csv")}
        r = requests.post(f"{BASE}/predict_batch", files=files, timeout=180)
    d = r.json()
    ok = r.status_code == 200 and "predictions" in d
    n = len(d.get("predictions", []))
    return ok, f"[{label}] rows={n} psi={d.get('overall_psi')} drift={d.get('drift_detected')} model={d.get('model_used')}"


def t_predict_batch_raw_schema(csv_path):
    """Deliberately raw/unclean CSV -- checking the silent-zero-fill hypothesis."""
    with open(csv_path, "rb") as f:
        files = {"file": (csv_path.split("/")[-1], f, "text/csv")}
        r = requests.post(f"{BASE}/predict_batch", files=files, timeout=60)
    d = r.json()
    ok = r.status_code == 200
    preds = d.get("predictions", [])
    avg_prob = sum(p.get("probability", 0) for p in preds) / len(preds) if preds else None
    return ok, f"status={r.status_code} rows={len(preds)} avg_prob={avg_prob} (raw schema, no error raised)"


def t_bad_csv():
    r = requests.post(f"{BASE}/predict_batch", files={"file": ("bad.txt", b"not,a,real,csv\njust text", "text/csv")}, timeout=30)
    return r.status_code in (400, 422), f"status={r.status_code} body={r.text[:200]}"


def t_empty_csv():
    r = requests.post(f"{BASE}/predict_batch", files={"file": ("empty.csv", b"", "text/csv")}, timeout=30)
    return r.status_code in (400, 422), f"status={r.status_code} body={r.text[:200]}"


def t_dashboard_metrics():
    r = requests.get(f"{BASE}/api/v1/dashboard-metrics", timeout=10)
    return r.status_code == 200, json.dumps(r.json())


def t_drift_history():
    r = requests.get(f"{BASE}/api/v1/drift-history", timeout=10)
    d = r.json()
    return r.status_code == 200, f"{len(d)} entries"


def t_models():
    r = requests.get(f"{BASE}/api/v1/models", timeout=10)
    return r.status_code == 200, json.dumps(r.json())


def t_llm_evaluations():
    r = requests.get(f"{BASE}/api/v1/llm-evaluations", timeout=10)
    d = r.json()
    return r.status_code == 200, f"{len(d)} entries"


def t_governance_log():
    r = requests.get(f"{BASE}/api/v1/governance-log", timeout=10)
    d = r.json()
    return r.status_code == 200, f"{len(d)} entries"


def t_fill_window(drift=False):
    r = requests.post(f"{BASE}/fill_window", params={"count": 30, "drift": str(drift).lower()}, timeout=30)
    return r.status_code == 200, json.dumps(r.json())[:200]


if __name__ == "__main__":
    print(f"=== Live smoke test against {BASE} ===\n")
    check("GET /api/health", t_health)
    check("GET /psi", t_psi)
    check("POST /predict (single row)", t_predict_single)
    check("POST /predict_batch (real 2000-row unseen batch)", lambda: t_predict_batch("dataset/live_test/real_applicants_batch.csv", "real 2000-row batch"))
    check("POST /predict_batch (real 20-row quick batch)", lambda: t_predict_batch("dataset/live_test/real_applicants_small.csv", "real 20-row batch"))
    check("POST /predict_batch (RAW untouched Kaggle schema)", lambda: t_predict_batch_raw_schema("dataset/live_test/raw_kaggle_schema_sample.csv"))
    check("POST /predict_batch (existing synthetic drift fixture)", lambda: t_predict_batch("dataset/test_drifted.csv", "synthetic drift fixture"))
    check("POST /predict_batch (malformed CSV -> should reject)", t_bad_csv)
    check("POST /predict_batch (empty CSV -> should reject)", t_empty_csv)
    check("GET /api/v1/dashboard-metrics", t_dashboard_metrics)
    check("GET /api/v1/drift-history", t_drift_history)
    check("GET /api/v1/models", t_models)
    check("GET /api/v1/llm-evaluations", t_llm_evaluations)
    check("GET /api/v1/governance-log", t_governance_log)
    check("POST /fill_window (no drift)", lambda: t_fill_window(False))

    n_pass = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n=== {n_pass}/{len(RESULTS)} passed ===")
