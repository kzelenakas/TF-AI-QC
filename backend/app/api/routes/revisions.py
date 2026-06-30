"""Revisions API Routes

POST   /reports/{report_id}/approve              — Approve report (reviewer, admin)
POST   /reports/{report_id}/request-revision     — Request revision (reviewer, admin)
POST   /revisions/{revision_id}/respond          — Appraiser responds to revision
GET    /reports/{report_id}/revisions            — Full revision history for a report
GET    /revisions/{revision_id}                  — Single revision detail

All endpoints require a valid Bubble auth token.
State transitions are enforced by the state machine — invalid transitions return 422.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user, require_reviewer
from app.core.database import get_db
from app.models.report import Report, ReportStatus
from app.models.revision import Revision, RevisionResponse
from app.services.workflow.state_machine import (
    TransitionError,
    add_revision_response,
    approve_report,
    request_revision,
)
from app.services.integrations.bubble_client import sync_report_status
from app.services.notifications import notify_approved, notify_revision_requested

router = APIRouter(tags=["revisions"])
logger = logging.getLogger(__name__)


# ── Response schemas ───────────────────────────────────────────────────────────

class RevisionResponseOut(BaseModel):
    id: str
    response_text: str
    responder_id: str
    created_at: str | None = None

    class Config:
        from_attributes = True


class RevisionOut(BaseModel):
    id: str
    report_id: str
    run_number: int
    notes: str
    status: str
    requested_by_id: str
    responses: list[RevisionResponseOut] = []
    created_at: str | None = None

    class Config:
        from_attributes = True


class ApproveResponse(BaseModel):
    report_id: str
    status: str
    message: str


class RequestRevisionBody(BaseModel):
    notes: str


class RequestRevisionResponse(BaseModel):
    revision_id: str
    report_id: str
    status: str
    message: str


class RespondBody(BaseModel):
    response_text: str


class RespondResponse(BaseModel):
    revision_id: str
    response_id: str
    message: str


# ── Helper ─────────────────────────────────────────────────────────────────────

def _get_report_or_404(report_id: str, db: Session) -> Report:
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


def _get_revision_or_404(revision_id: str, db: Session) -> Revision:
    revision = db.query(Revision).filter(Revision.id == revision_id).first()
    if not revision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    return revision


def _build_revision_out(rev: Revision) -> RevisionOut:
    response_outs = [
        RevisionResponseOut(
            id=r.id,
            response_text=r.response_text,
            responder_id=r.responder_id,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rev.responses
    ]
    return RevisionOut(
        id=rev.id,
        report_id=rev.report_id,
        run_number=rev.run_number,
        notes=rev.notes,
        status=rev.status.value,
        requested_by_id=rev.requested_by_id,
        responses=response_outs,
        created_at=rev.created_at.isoformat() if rev.created_at else None,
    )


# ── POST /reports/{report_id}/approve ─────────────────────────────────────────

@router.post("/reports/{report_id}/approve", response_model=ApproveResponse)
async def approve(
    report_id: str,
    current_user: CurrentUser = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """
    Approve a report that has completed QC.
    Closes any open revisions. Reviewer/admin only.
    """
    report = _get_report_or_404(report_id, db)

    if report.status != ReportStatus.qc_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Report must be in qc_complete status to approve (current: {report.status.value})",
        )

    try:
        approve_report(report, current_user, db)
        db.commit()
    except TransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    logger.info(
        "Report approved",
        extra={"report_id": report_id, "reviewer_id": current_user.user_id},
    )

    # Non-blocking side effects
    await sync_report_status(report_id, "approved")
    from app.models.user import User
    from app.models.qc_result import QCResult
    uploader = db.query(User).filter(User.id == report.uploader_id).first()
    latest_qc = db.query(QCResult).filter(QCResult.report_id == report_id).order_by(QCResult.run_number.desc()).first()
    if uploader and uploader.email:
        await notify_approved(uploader.email, report_id, latest_qc.quality_score if latest_qc else None)

    return ApproveResponse(
        report_id=report_id,
        status="approved",
        message="Report approved.",
    )


# ── POST /reports/{report_id}/request-revision ────────────────────────────────

@router.post("/reports/{report_id}/request-revision", response_model=RequestRevisionResponse, status_code=status.HTTP_201_CREATED)
async def create_revision_request(
    report_id: str,
    body: RequestRevisionBody,
    current_user: CurrentUser = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """
    Request revisions on a QC-complete report.
    Creates a Revision record, transitions report to revision_requested.
    Reviewer/admin only.
    """
    report = _get_report_or_404(report_id, db)

    if report.status != ReportStatus.qc_complete:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Report must be in qc_complete status to request revision (current: {report.status.value})",
        )

    try:
        revision = request_revision(
            report=report,
            actor=current_user,
            notes=body.notes,
            db=db,
        )
        db.commit()
        db.refresh(revision)
    except TransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    logger.info(
        "Revision requested",
        extra={"report_id": report_id, "revision_id": revision.id, "reviewer_id": current_user.user_id},
    )

    # Non-blocking side effects
    await sync_report_status(report_id, "revision_requested")
    from app.models.user import User
    uploader = db.query(User).filter(User.id == report.uploader_id).first()
    if uploader and uploader.email:
        await notify_revision_requested(uploader.email, report_id, body.notes)

    return RequestRevisionResponse(
        revision_id=revision.id,
        report_id=report_id,
        status="revision_requested",
        message="Revision request created. Appraiser will be notified.",
    )


# ── POST /revisions/{revision_id}/respond ────────────────────────────────────

@router.post("/revisions/{revision_id}/respond", response_model=RespondResponse, status_code=status.HTTP_201_CREATED)
def respond_to_revision(
    revision_id: str,
    body: RespondBody,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Appraiser submits a response to an open revision request.
    Only the original report uploader may respond (or admin).
    """
    revision = _get_revision_or_404(revision_id, db)

    # Authorization — only uploader or admin
    if not current_user.is_admin:
        from app.models.user import User
        user_record = db.query(User).filter(User.bubble_user_id == current_user.user_id).first()
        report = db.query(Report).filter(Report.id == revision.report_id).first()
        if not user_record or not report or report.uploader_id != user_record.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the original uploader may respond to this revision",
            )

    try:
        response = add_revision_response(
            revision=revision,
            actor=current_user,
            response_text=body.response_text,
            db=db,
        )
        db.commit()
        db.refresh(response)
    except TransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return RespondResponse(
        revision_id=revision_id,
        response_id=response.id,
        message="Response recorded. Upload a revised report to resubmit.",
    )


# ── GET /reports/{report_id}/revisions ────────────────────────────────────────

@router.get("/reports/{report_id}/revisions", response_model=list[RevisionOut])
def list_revisions(
    report_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full revision history for a report. Appraisers see only their own."""
    report = _get_report_or_404(report_id, db)

    if current_user.is_appraiser:
        from app.models.user import User
        user_record = db.query(User).filter(User.bubble_user_id == current_user.user_id).first()
        if not user_record or report.uploader_id != user_record.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    revisions = (
        db.query(Revision)
        .filter(Revision.report_id == report_id)
        .order_by(Revision.run_number.desc(), Revision.created_at.desc())
        .all()
    )

    return [_build_revision_out(r) for r in revisions]


# ── GET /revisions/{revision_id} ──────────────────────────────────────────────

@router.get("/revisions/{revision_id}", response_model=RevisionOut)
def get_revision(
    revision_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single revision with all responses."""
    revision = _get_revision_or_404(revision_id, db)

    if current_user.is_appraiser:
        from app.models.user import User
        user_record = db.query(User).filter(User.bubble_user_id == current_user.user_id).first()
        report = db.query(Report).filter(Report.id == revision.report_id).first()
        if not user_record or not report or report.uploader_id != user_record.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _build_revision_out(revision)
