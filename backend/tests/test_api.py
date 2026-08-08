"""
Integration tests for the FastAPI endpoints, running against the real app
(real startup event, real committed Models/*.pkl) but with the baseline
pointed at a small synthetic fixture and all external calls (Databricks,
LLMs) stubbed out via conftest.py's `client` fixture.
"""
import io


def test_health_reports_models_and_baseline_loaded(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["model_loaded"] is True
    assert body["challenger_loaded"] is True
    assert body["baseline_loaded"] is True
    assert body["features_count"] == 20


def test_predict_single_row_returns_full_response_shape(client):
    resp = client.post("/predict", json={})  # every field has a schema default
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "psi" in body
    assert "psi_per_feature" in body
    assert isinstance(body["drift_detected"], bool)
    assert body["model_used"] in ("Champion", "Challenger")
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_label"] in ("Low", "Medium", "High")
    assert body["decision"] in ("Accept Loan", "Reject Loan")
    assert body["explanation_llm"] == "llama"  # from the conftest stub


def test_predict_high_risk_input_rejects(client):
    resp = client.post("/predict", json={
        "AMT_INCOME_TOTAL": 50000.0,
        "AMT_CREDIT_x": 900000.0,
        "AMT_ANNUITY": 60000.0,
        "EXT_SOURCE_1": 0.02,
        "EXT_SOURCE_2": 0.02,
        "EXT_SOURCE_3": 0.02,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["risk_label"] in ("Medium", "High")


def _csv_bytes(rows: list[dict]) -> bytes:
    import pandas as pd
    return pd.DataFrame(rows).to_csv(index=False).encode()


def test_predict_batch_valid_csv_returns_full_response_shape(client):
    rows = [
        {"AMT_INCOME_TOTAL": 200000, "AMT_CREDIT_x": 500000, "AMT_ANNUITY": 25000,
         "EXT_SOURCE_1": 0.5, "EXT_SOURCE_2": 0.5, "EXT_SOURCE_3": 0.5}
        for _ in range(10)
    ]
    files = {"file": ("batch.csv", io.BytesIO(_csv_bytes(rows)), "text/csv")}
    resp = client.post("/predict_batch", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["total_rows"] == 10
    assert len(body["predictions"]) == 10
    assert "risk_distribution" in body
    assert set(body["risk_distribution"].keys()) == {"Low", "Medium", "High"}
    assert sum(body["risk_distribution"].values()) == 10


def test_predict_batch_rejects_non_csv_file(client):
    files = {"file": ("data.txt", io.BytesIO(b"not a csv"), "text/plain")}
    resp = client.post("/predict_batch", files=files)
    assert resp.status_code == 200  # app returns a JSON error body, not an HTTP error
    body = resp.json()
    assert body["status"] == "failed"
    assert "csv" in body["error"].lower()


def test_predict_batch_rejects_empty_csv(client):
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    resp = client.post("/predict_batch", files=files)
    body = resp.json()
    assert body["status"] == "failed"
    assert "empty" in body["error"].lower()


def test_predict_batch_rejects_malformed_csv(client):
    # Inconsistent column counts across rows -- a real parser error, not
    # just an empty/valid-but-useless file.
    malformed = b"a,b,c\n1,2\n3,4,5,6,7\n"
    files = {"file": ("malformed.csv", io.BytesIO(malformed), "text/csv")}
    resp = client.post("/predict_batch", files=files)
    body = resp.json()
    assert body["status"] == "failed"
    assert "Invalid CSV" in body["error"]


def test_drift_detected_switches_to_challenger(client):
    """Feed a batch far outside the fixture baseline's ranges on every PSI
    feature at once -- should push overall PSI past the 0.25 threshold."""
    rows = [
        {"AMT_INCOME_TOTAL": 5000000, "AMT_CREDIT_x": 8000000, "AMT_ANNUITY": 400000,
         "DAYS_EMPLOYED": -1, "EXT_SOURCE_1": 0.99, "EXT_SOURCE_2": 0.99, "EXT_SOURCE_3": 0.99}
        for _ in range(20)
    ]
    files = {"file": ("drifted.csv", io.BytesIO(_csv_bytes(rows)), "text/csv")}
    resp = client.post("/predict_batch", files=files)
    body = resp.json()
    assert body["status"] == "success"
    assert body["drift_detected"] is True
    assert body["model_used"] == "Challenger"
    assert body["psi"] >= 0.25


def test_psi_endpoint_reports_configured_features(client):
    resp = client.get("/psi")
    body = resp.json()
    assert body["baseline_loaded"] is True
    assert body["threshold"] == 0.25
    assert len(body["active_features"]) >= 5  # spec requires >= 5 PSI features
