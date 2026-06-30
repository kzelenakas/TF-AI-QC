"""Reports API Routes

POST   /reports                   — Upload a new appraisal report (appraiser+)
GET    /reports                   — List reports (role-filtered)
GET    /reports/{report_id}       — Get report detail + latest QC result
GET    /reports/{report_id}/file  — Get presigned download URL (audit logged)
POST   /reports/{report_id}/resubmit — Resubmit after revision request (appraiser)

All endpoints require a valid Bubble auth token (Authorization: Bearer <token>).
QC runs as a FastAPI BackgroundTask — upload returns 202 immediately.

SECURITY:
- Presigned URLs only — never expose R2 object keys in responses
- No PII in response bodies except to authorized roles
- All NPI access (file download) is audit-logged
- Appraisers see only their own reports
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.storage import generate_presigned_url
from app.models.qc_result import QCFlag, QCResult
from app.models.report import Report, ReportStatus
from app.services.qc_service import (
    _audit,
    process_resubmission,
    process_upload,
    run_qc_pipeline,
)

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)


class FlagOut(BaseModel):
    id: str
    severity: str
    field_name: str
    message: str
    value_found: str | None = None
    value_expected: str | None = None
    rule_code: str | None = None
    class Config:
        from_attributes = True


class QCResultOut(BaseModel):
    id: str
    run_number: int
    pass_fail: bool
    quality_score: int | None
    score_breakdown: dict | None
    error_count: int
    warning_count: int
    flags: list[FlagOut]
    class Config:
        from_attributes = True


class ReportOut(BaseModel):
    id: str
    status: str
    file_type: str
    file_size: int
    original_filename: str
    run_number: int
    property_address: str | None = None
    borrower_name: str | None = None
    latest_qc: QCResultOut | None = None
    created_at: str | None = None
    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    id: str
    status: str
    file_type: str
    file_size: int
    original_filename: str
    run_number: int
    property_address: str | None = None
    quality_score: int | None = None
    pass_fail: bool | None = None
    created_at: str | None = None
    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    report_id: str
    status: str
    message: str


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in_seconds: int


def _build_qc_result_out(qc: QCResult, flags: list[QCFlag]) -> QCResultOut:
    flag_outs = [
        FlagOut(
            id=f.id, severity=f.severity.value, field_name=f.field_name,
            message=f.message, value_found=f.value_found, value_expected=f.value_expected,
            rule_code=f.rule.code if f.rule else None,
        )
        for f in flags
    ]
    return QCResultOut(
        id=qc.id, run_number=qc.run_number, pass_fail=qc.pass_fail,
        quality_score=qc.quality_score, score_breakdown=qc.score_breakdown,
        error_count=sum(1 for f in flags if f.severity.value == "error"),
        warning_count=sum(1 for f in flags if f.severity.value == "warning"),
        flags=flag_outs,
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=UploadResponse)
async def upload_report(file: UploadFile, background_tasks: BackgroundTasks, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    file_bytes = await file.read()
    try:
        report = await process_upload(file_bytes=file_bytes, original_filename=file.filename or "upload", uploader=current_user, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    from app.core.database import SessionLocal
    async def _run_qc_with_own_session():
        bg_db = SessionLocal()
        try:
            await run_qc_pipeline(report.id, file_bytes, bg_db)
        finally:
            bg_db.close()

    background_tasks.add_task(_run_qc_with_own_session)
    logger.info("Upload accepted, QC queued", extra={"report_id": report.id, "user_id": current_user.user_id})
    return UploadResponse(report_id=report.id, status="submitted", message="Report uploaded. QC is running in the background.")


@router.get("", response_model=list[ReportListItem])
def list_reports(status_filter: str | None = Query(None, alias="status"), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.user import User
    user_record = db.query(User).filter(User.bubble_user_id == current_user.user_id).first()
    if not user_record:
        return []
    query = db.query(Report)
    if current_user.is_appraiser:
        query = query.filter(Report.uploader_id == user_record.id)
    if status_filter:
        try:
            s = ReportStatus(status_filter)
            query = query.filter(Report.status == s)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status '{status_filter}'")
    reports = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()
    result = []
    for r in reports:
        latest_qc = db.query(QCResult).filter(QCResult.report_id == r.id).order_by(QCResult.run_number.desc()).first()
        result.append(ReportListItem(id=r.id, status=r.status.value, file_type=r.file_type.value, file_size=r.file_size, original_filename=r.original_filename, run_number=r.run_number, property_address=r.property_address, quality_score=latest_qc.quality_score if latest_qc else None, pass_fail=latest_qc.pass_fail if latest_qc else None, created_at=r.created_at.isoformat() if r.created_at else None))
    return result


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.user import User
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if current_user.is_appraiser:
        user_record = db.query(User).filter(User.bubble_user_id == current_user.user_id).first()
        if not user_record or report.uploader_id != user_record.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    _audit("report_viewed", user_id=current_user.user_id, report_id=report_id)
    latest_qc = db.query(QCResult).filter(QCResult.report_id == report_id).order_by(QCResult.run_number.desc()).first()
    qc_out = None
    if latest_qc:
        flags = db.query(QCFlag).filter(QCFlag.qc_result_id == latest_qc.id).all()
        qc_out = _build_qc_result_out(latest_qc, flags)
    return ReportOut(id=report.id, status=report.status.value, file_type=report.file_type.value, file_size=report.file_size, original_filename=report.original_filename, run_number=report.run_number, property_address=report.property_address, borrower_name=report.borrower_name, latest_qc=qc_out, created_at=report.created_at.isoformat() if report.created_at else None)


@router.get("/{report_id}/file", response_model=DownloadUrlResponse)
def get_report_download_url(report_id: str, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.user import User
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if current_user.is_appraiser:
        user_record = db.query(User).filter(User.bubble_user_id == current_user.user_id).first()
        if not user_record or report.uploader_id != user_record.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    presigned_url = generate_presigned_url(report.file_url, expiry_seconds=900)
    _audit("report_file_downloaded", user_id=current_user.user_id, report_id=report_id, file_type=report.file_type.value)
    return DownloadUrlResponse(url=presigned_url, expires_in_seconds=900)


@router.post("/{report_id}/resubmit", status_code=status.HTTP_202_ACCEPTED, response_model=UploadResponse)
async def resubmit_report(report_id: str, file: UploadFile, background_tasks: BackgroundTasks, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    file_bytes = await file.read()
    try:
        report = await process_resubmission(report_id=report_id, file_bytes=file_bytes, original_filename=file.filename or "resubmission", uploader=current_user, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    from app.core.database import SessionLocal
    async def _run_qc_with_own_session():
        bg_db = SessionLocal()
        try:
            await run_qc_pipeline(report.id, file_bytes, bg_db)
        finally:
            bg_db.close()

    background_tasks.add_task(_run_qc_with_own_session)
    return UploadResponse(report_id=report.id, status="resubmitted", message=f"Report resubmitted (run #{report.run_number}). QC is running.")
