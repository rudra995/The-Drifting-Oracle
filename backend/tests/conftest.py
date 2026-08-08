"""
Shared fixtures for the API test suite.

Key design point: tests must never touch the real Databricks workspace,
even when run on a machine whose .env has real credentials in it (a CI
runner won't have .env at all, but a developer's laptop will). The
`client` fixture forces databricks_io off explicitly rather than relying
on the environment being clean, so test runs are hermetic either way.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

import config


@pytest.fixture
def client(monkeypatch):
    # Point the baseline loader at the small synthetic fixture instead of
    # the real (gitignored, 49MB) production dataset.
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "mini_baseline.csv")
    monkeypatch.setattr(config, "BASELINE_PATHS", [fixture_path])

    # Never let a test write to the real Delta tables, regardless of what
    # credentials happen to be sitting in .env on whoever's machine runs this.
    import databricks_io
    monkeypatch.setattr(databricks_io, "ENABLED", False)

    # Deterministic, fast, offline LLM responses -- a test shouldn't depend on
    # a local Ollama instance or a real Gemini key being reachable.
    import llm_explanation
    monkeypatch.setattr(
        llm_explanation, "call_llama",
        lambda prompt: ("Test explanation: within normal parameters.", "llama"),
    )

    from main import app
    with TestClient(app) as test_client:
        yield test_client
