"""
Smoke tests — verify the FastAPI app starts and health endpoints respond.
Run with: pytest backend/tests/test_health.py -v
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "tf-ai-qc"
