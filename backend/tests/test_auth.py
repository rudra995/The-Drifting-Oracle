"""
Tests for the minimal API-key auth gate (main.py's require_api_key
middleware, config.API_KEY). Reuses the same `client` fixture as the rest
of the API suite -- conftest.py doesn't set config.API_KEY, so it's None
there by default (the open, zero-config local-dev behavior); these tests
monkeypatch it per-case to exercise the gated behavior too.
"""
import config


def test_requests_pass_through_when_api_key_is_unset(client):
    # conftest's client fixture never sets config.API_KEY -- default is None.
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_missing_key_is_rejected_once_api_key_is_set(client, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "secret123")
    resp = client.get("/psi")
    assert resp.status_code == 401
    assert resp.json()["status"] == "failed"


def test_wrong_key_is_rejected(client, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "secret123")
    resp = client.get("/psi", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


def test_correct_key_is_accepted(client, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "secret123")
    resp = client.get("/psi", headers={"X-API-Key": "secret123"})
    assert resp.status_code == 200


def test_health_check_is_exempt_even_without_a_key(client, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "secret123")
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_root_is_exempt_even_without_a_key(client, monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "secret123")
    resp = client.get("/")
    assert resp.status_code == 200
