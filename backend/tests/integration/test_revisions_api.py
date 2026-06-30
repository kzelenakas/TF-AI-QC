"""Integration tests for the revision workflow API."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.models.qc_result import QCResult
from app.models.report import Report, ReportStatus
from app.models.user import User, UserRole


def _seed_report(db_session, uploader_id: str, status: ReportStatus = ReportStatus.qc_complete) -> Report:
    report = Report(
        uploader_id=uploader_id,
        file_url="test/report.xml",
        file_type="xml",
        file_size=1024,
        original_filename="report.xml",
        status=status,
        run_number=1,
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


def _seed_user(db_session, bubble_id: str = "test-bubble-id", role: str = "appraiser") -> User:
    user = User(
        bubble_user_id=bubble_id,
        email=f"{bubble_id}@truefootage.com",
        name="Test User",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestApproveReport:
    def test_reviewer_can_approve(self, client_reviewer, db_session):
        uploader = _seed_user(db_session, bubble_id="test-bubble-id")
        report = _seed_report(db_session, uploader_id=uploader.id)
        with patch("app.api.routes.revisions.sync_report_status", new_callable=AsyncMock), \
             patch("app.api.routes.revisions.notify_approved", new_callable=AsyncMock):
            resp = client_reviewer.post(f"/reports/{report.id}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_approve_wrong_status_422(self, client_reviewer, db_session):
        uploader = _seed_user(db_session)
        report = _seed_report(db_session, uploader_id=uploader.id, status=ReportStatus.submitted)
        resp = client_reviewer.post(f"/reports/{report.id}/approve")
        assert resp.status_code == 422

    def test_appraiser_cannot_approve(self, client_appraiser, db_session):
        uploader = _seed_user(db_session)
        report = _seed_report(db_session, uploader_id=uploader.id)
        resp = client_appraiser.post(f"/reports/{report.id}/approve")
        assert resp.status_code == 403


class TestRequestRevision:
    def test_reviewer_can_request_revision(self, client_reviewer, db_session):
        uploader = _seed_user(db_session)
        report = _seed_report(db_session, uploader_id=uploader.id)
        with patch("app.api.routes.revisions.sync_report_status", new_callable=AsyncMock), \
             patch("app.api.routes.revisions.notify_revision_requested", new_callable=AsyncMock):
            resp = client_reviewer.post(
                f"/reports/{report.id}/request-revision",
                json={"notes": "Please fix the net adjustments on Comp 2."},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "revision_requested"
        assert "revision_id" in data

    def test_missing_notes_rejected(self, client_reviewer, db_session):
        uploader = _seed_user(db_session)
        report = _seed_report(db_session, uploader_id=uploader.id)
        resp = client_reviewer.post(
            f"/reports/{report.id}/request-revision",
            json={},
        )
        assert resp.status_code == 422


class TestListRevisions:
    def test_empty_revision_list(self, client_reviewer, db_session):
        uploader = _seed_user(db_session)
        report = _seed_report(db_session, uploader_id=uploader.id)
        resp = client_reviewer.get(f"/reports/{report.id}/revisions")
        assert resp.status_code == 200
        assert resp.json() == []
