"""QC Service — orchestrates the full report QC pipeline.

Pipeline:
  1. Validate file (magic bytes)
  2. Upload to Cloudflare R2 (returns object key)
  3. Create Report record in DB (status=submitted)
  4. Extract ReportData via ingest factory
  5. Update status to qc_running
  6. Run two-pass rule engine (Pass 1 compliance + Pass 2 quality)
  7. Persist QCResult + QCFlags
  8. Update status to qc_complete
  9. Bubble OMS sync + reviewer email (non-blocking)

Called from the reports router. QC runs as a FastAPI BackgroundTask so
the upload endpoint returns 202 immediately while QC runs in the background.

SECURITY:
- PII never written to logs (only report_id, file_type, file_size, run_number)
- file_url stored as R2 object key only — signed URLs generated at request time
- All NPI access is audit-logged
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.storage import upload_report
from app.models.qc_result import FlagSeverity, QCFlag, QCResult
from app.models.report import FileType, Report, ReportStatus
from app.models.rule import Rule
from app.services.ingest.extractor_factory import detect_file_type, extract
from app.services.rules.engine import EngineResult, get_engine
from app.services.integrations.bubble_client import sync_report_status
from app.services.notifications import notify_qc_complete

logger = logging.getLogger(__name__)

# ── Audit logger (structured, no PII) ──────────────────────────────────────────

audit_logger = logging.getLogger("audit")


def _audit(action: str, user_id: str, report_id: str, **extra: Any) -> None:
    """Emit an audit log entry. Never include PII in kwargs."""
    audit_logger.info(
        action,
        extra={
            "user_id": user_id,
            "report_id": report_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra,
        },
    )


# ── File validation ────────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def validate_file(file_bytes: bytes, original_filename: str) -> str:
    """
    Validate uploaded file via magic bytes (not filename/extension).
    Returns detected file type string ("xml" or "pdf").
    Raises ValueError on invalid file.
    """
    if len(file_bytes) == 0:
        raise ValueError("File is empty")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // 1024 // 1024} MB")

    try:
        file_type = detect_file_type(file_bytes)
    except ValueError:
        raise ValueError(
            f"Unsupported file type. Only UAD 3.6 XML and URAR PDF files are accepted. "
            f"Filename: {original_filename}"
        )
    return file_type


# ── Rule ID lookup cache ───────────────────────────────────────────────────────

_rule_code_to_id: dict[str, str] = {}
_rule_cache_ts: float = 0.0


def _get_rule_id_map(db: Session) -> dict[str, str]:
    """Map rule code → DB rule.id. Cached for 5 minutes."""
    import time
    global _rule_code_to_id, _rule_cache_ts
    if _rule_code_to_id and (time.monotonic() - _rule_cache_ts) < 300:
        return _rule_code_to_id
    rows = db.query(Rule.code, Rule.id).all()
    _rule_code_to_id = {r.code: r.id for r in rows}
    _rule_cache_ts = time.monotonic()
    return _rule_code_to_id


# ── Core pipeline ──────────────────────────────────────────────────────────────

async def run_qc_pipeline(report_id: str, file_bytes: bytes, db: Session) -> None:
    """
    Execute the full QC pipeline for an uploaded report.

    Called as a FastAPI BackgroundTask — runs after the upload endpoint returns 202.
    Updates report.status throughout. Errors are caught and logged; report status
    is set back to submitted so the uploader can retry.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        logger.error("run_qc_pipeline: report not found", extra={"report_id": report_id})
        return

    logger.info(
        "QC pipeline starting",
        extra={
            "report_id": report_id,
            "file_type": report.file_type,
            "file_size": report.file_size,
            "run_number": report.run_number,
        },
    )

    # ── Step 1: Mark qc_running ────────────────────────────────────────────────
    report.status = ReportStatus.qc_running
    db.commit()

    try:
        # ── Step 2: Parse report ───────────────────────────────────────────────
        report_data, _ = extract(file_bytes)

        # ── Step 3: Run rule engine ────────────────────────────────────────────
        engine = get_engine()
        result: EngineResult = await engine.evaluate(report_data, db)

        # ── Step 4: Persist QCResult ───────────────────────────────────────────
        qc_result = QCResult(
            report_id=report_id,
            run_number=report.run_number,
            pass_fail=result.pass1_passed,
            quality_score=result.quality_score,
            score_breakdown=result.score_breakdown,
            raw_flags=result.to_raw_flags_jsonb(),
        )
        db.add(qc_result)
        db.flush()  # get qc_result.id without committing

        # ── Step 5: Persist QCFlags ────────────────────────────────────────────
        rule_id_map = _get_rule_id_map(db)

        for flag in result.all_rule_flags:
            severity = FlagSeverity(flag.severity) if flag.severity in FlagSeverity.__members__ else FlagSeverity.warning
            db.add(QCFlag(
                qc_result_id=qc_result.id,
                rule_id=rule_id_map.get(flag.rule_code),  # None if rule not in DB
                severity=severity,
                field_name=flag.field_name[:255],
                message=flag.message[:1024],
                value_found=(flag.value_found or "")[:512] or None,
                value_expected=(flag.value_expected or "")[:512] or None,
            ))

        # Quality flags (Pass 2) — no rule_id, severity=info
        for qflag in result.quality_flags:
            db.add(QCFlag(
                qc_result_id=qc_result.id,
                rule_id=None,
                severity=FlagSeverity.info,
                field_name=qflag.get("field", "quality")[:255],
                message=qflag.get("issue", "")[:1024],
            ))

        # ── Step 6: Update report status + address (display only) ──────────────
        report.status = ReportStatus.qc_complete
        if report_data.subject_full_address:
            report.property_address = report_data.subject_full_address
        if getattr(report_data, "borrower_name", None):
            report.borrower_name = report_data.borrower_name

        db.commit()

        _audit(
            "qc_complete",
            user_id=report.uploader_id,
            report_id=report_id,
            pass_fail=result.pass1_passed,
            quality_score=result.quality_score,
            error_count=len(result.pass1_error_flags),
            warning_count=len(result.pass1_warning_flags),
            run_number=report.run_number,
        )

        # ── Step 7: Non-blocking side effects ─────────────────────────────────
        # Bubble OMS sync
        await sync_report_status(
            report_id=report_id,
            new_status="qc_complete",
            quality_score=result.quality_score,
            pass_fail=result.pass1_passed,
        )

        # Reviewer email notification
        from app.core.config import settings
        if settings.reviewer_notify_email:
            for reviewer_email in [e.strip() for e in settings.reviewer_notify_email.split(",") if e.strip()]:
                await notify_qc_complete(
                    reviewer_email=reviewer_email,
                    report_id=report_id,
                    pass_fail=result.pass1_passed,
                    quality_score=result.quality_score,
                    error_count=len(result.pass1_error_flags),
                )

        logger.info(
            "QC pipeline complete",
            extra={
                "report_id": report_id,
                "pass1_passed": result.pass1_passed,
                "quality_score": result.quality_score,
                "run_number": report.run_number,
            },
        )

    except Exception as e:
        db.rollback()
        logger.error(
            "QC pipeline failed",
            extra={"report_id": report_id, "error": str(e)},
            exc_info=True,
        )
        # Reset to submitted so uploader can retry
        try:
            report.status = ReportStatus.submitted
            db.commit()
        except Exception:
            db.rollback()


async def process_upload(
    file_bytes: bytes,
    original_filename: str,
    uploader: CurrentUser,
    db: Session,
) -> Report:
    """
    Validate + upload file to R2, create Report record.
    Does NOT run QC — caller must schedule run_qc_pipeline as a background task.

    Returns the newly created Report (status=submitted).
    """
    # Validate
    file_type_str = validate_file(file_bytes, original_filename)
    file_type = FileType(file_type_str)

    # Get or create User record
    from app.models.user import User
    user_record = db.query(User).filter(User.bubble_user_id == uploader.user_id).first()
    if not user_record:
        user_record = User(
            bubble_user_id=uploader.user_id,
            email=uploader.email,
            name=uploader.email.split("@")[0],
            role=uploader.role,
        )
        db.add(user_record)
        db.flush()

    # Upload to R2
    object_key = upload_report(
        file_bytes=file_bytes,
        filename=original_filename,
        content_type="application/xml" if file_type == FileType.xml else "application/pdf",
        user_id=user_record.id,
    )

    # Create report record
    report = Report(
        uploader_id=user_record.id,
        file_url=object_key,
        file_type=file_type,
        file_size=len(file_bytes),
        original_filename=original_filename,
        status=ReportStatus.submitted,
        run_number=1,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    _audit(
        "report_uploaded",
        user_id=user_record.id,
        report_id=report.id,
        file_type=file_type.value,
        file_size=len(file_bytes),
    )

    logger.info(
        "Report uploaded",
        extra={
            "report_id": report.id,
            "file_type": file_type.value,
            "file_size": len(file_bytes),
            "user_id": user_record.id,
        },
    )

    return report


async def process_resubmission(
    report_id: str,
    file_bytes: bytes,
    original_filename: str,
    uploader: CurrentUser,
    db: Session,
) -> Report:
    """
    Handle a resubmission — increment run_number, upload new file, reset to submitted.
    Caller schedules run_qc_pipeline as background task.
    """
    from app.models.user import User

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise ValueError(f"Report {report_id} not found")

    user_record = db.query(User).filter(User.bubble_user_id == uploader.user_id).first()
    if not user_record:
        raise ValueError("User not found")

    # Only the original uploader may resubmit
    if report.uploader_id != user_record.id and uploader.role not in ("reviewer", "admin"):
        raise PermissionError("Only the original uploader may resubmit this report")

    # Only revision_requested status allows resubmission
    if report.status != ReportStatus.revision_requested:
        raise ValueError(f"Report must be in revision_requested status to resubmit (current: {report.status})")

    # Validate new file
    file_type_str = validate_file(file_bytes, original_filename)
    file_type = FileType(file_type_str)

    # Upload new file
    object_key = upload_report(
        file_bytes=file_bytes,
        filename=original_filename,
        content_type="application/xml" if file_type == FileType.xml else "application/pdf",
        user_id=user_record.id,
    )

    # Increment run_number, update file reference
    report.run_number += 1
    report.file_url = object_key
    report.file_type = file_type
    report.file_size = len(file_bytes)
    report.original_filename = original_filename
    report.status = ReportStatus.resubmitted
    db.commit()
    db.refresh(report)

    _audit(
        "report_resubmitted",
        user_id=user_record.id,
        report_id=report_id,
        file_type=file_type.value,
        file_size=len(file_bytes),
        run_number=report.run_number,
    )

    return report
