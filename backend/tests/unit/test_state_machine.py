"""Tests for the report lifecycle state machine."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.core.auth import CurrentUser
from app.models.report import Report, ReportStatus
from app.services.workflow.state_machine import TransitionError, approve_report, request_revision


def _mock_report(status: ReportStatus) -> Report:
    report = MagicMock(spec=Report)
    report.status = status
    report.id = "test-report-id"
    return report


def _reviewer() -> CurrentUser:
    return CurrentUser(user_id="reviewer-1", role="reviewer")


class TestApprovReport:
    def test_approve_from_qc_complete(self, db_session):
        report = _mock_report(ReportStatus.qc_complete)
        approve_report(report, _reviewer(), db_session)
        assert report.status == ReportStatus.approved

    def test_approve_from_wrong_status_raises(self, db_session):
        report = _mock_report(ReportStatus.submitted)
        with pytest.raises(TransitionError):
            approve_report(report, _reviewer(), db_session)

    def test_appraiser_cannot_approve(self, db_session):
        report = _mock_report(ReportStatus.qc_complete)
        appraiser = CurrentUser(user_id="appraiser-1", role="appraiser")
        with pytest.raises(TransitionError):
            approve_report(report, appraiser, db_session)


class TestRequestRevision:
    def test_request_from_qc_complete(self, db_session):
        report = _mock_report(ReportStatus.qc_complete)
        revision = request_revision(report, _reviewer(), "Fix the adjustments.", db_session)
        assert report.status == ReportStatus.revision_requested
        assert revision is not None

    def test_request_from_wrong_status_raises(self, db_session):
        report = _mock_report(ReportStatus.approved)
        with pytest.raises(TransitionError):
            request_revision(report, _reviewer(), "notes", db_session)
