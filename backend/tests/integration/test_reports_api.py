"""Integration tests for the reports API.

Uses SQLite in-memory DB and mocked R2/Ollama (from conftest fixtures).
Does NOT test QC pipeline end-to-end — that requires Ollama + real rules.
Focuses on: upload validation, auth enforcement, list/get filtering.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.models.report import ReportStatus
from app.models.user import User, UserRole


XML_BYTES = b"<?xml version=\"1.0\"?><root/>"
PDF_BYTES = b"%PDF-1.4 fake"
PNG_BYTES = b"\x89PNG\r\n\x1a\n fake"


class TestUploadReport:
    def test_upload_xml_returns_202(self, client_appraiser, db_session):
        with patch("app.api.routes.reports.run_qc_pipeline", new_callable=AsyncMock):
            resp = client_appraiser.post(
                "/reports",
                files={"file": ("report.xml", XML_BYTES, "application/xml")},
            )
        assert resp.status_code == 202
        data = resp.json()
        assert "report_id" in data
        assert data["status"] == "submitted"

    def test_upload_pdf_returns_202(self, client_appraiser):
        with patch("app.api.routes.reports.run_qc_pipeline", new_callable=AsyncMock):
            resp = client_appraiser.post(
                "/reports",
                files={"file": ("report.pdf", PDF_BYTES, "application/pdf")},
            )
        assert resp.status_code == 202

    def test_upload_invalid_type_rejected(self, client_appraiser):
        resp = client_appraiser.post(
            "/reports",
            files={"file": ("image.png", PNG_BYTES, "image/png")},
        )
        assert resp.status_code == 422

    def test_upload_empty_file_rejected(self, client_appraiser):
        resp = client_appraiser.post(
            "/reports",
            files={"file": ("empty.xml", b"", "application/xml")},
        )
        assert resp.status_code == 422

    def test_upload_requires_auth(self):
        """Endpoint must reject requests with no auth token."""
        from fastapi.testclient import TestClient
        from app.main import app
        plain_client = TestClient(app)
        resp = plain_client.post(
            "/reports",
            files={"file": ("report.xml", XML_BYTES, "application/xml")},
        )
        assert resp.status_code == 403


class TestListReports:
    def test_reviewer_can_list_all(self, client_reviewer):
        resp = client_reviewer.get("/reports")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_appraiser_can_list_own(self, client_appraiser):
        resp = client_appraiser.get("/reports")
        assert resp.status_code == 200


class TestGetReport:
    def test_missing_report_returns_404(self, client_reviewer):
        resp = client_reviewer.get("/reports/nonexistent-id")
        assert resp.status_code == 404
