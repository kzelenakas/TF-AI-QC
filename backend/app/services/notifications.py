"""Notification Service — Resend email.

Sends email on: QC complete (to reviewer), revision requested (to appraiser), approved (to appraiser).
Emails contain report_id and status only — no NPI.
If Resend not configured, skipped silently.
"""
from __future__ import annotations
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
RESEND_API_URL = "https://api.resend.com/emails"
FROM_ADDRESS = "TF AI-QC <noreply@truefootage.com>"
TIMEOUT_SECONDS = 10


async def _send(to: str, subject: str, html: str) -> bool:
    if not settings.resend_api_key:
        logger.debug("Notifications skipped — RESEND_API_KEY not configured")
        return False
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            resp = await client.post(RESEND_API_URL, json={"from": FROM_ADDRESS, "to": [to], "subject": subject, "html": html}, headers={"Authorization": f"Bearer {settings.resend_api_key}"})
        ok = resp.status_code in (200, 201)
        if not ok:
            logger.warning("Email send failed", extra={"http_status": resp.status_code})
        return ok
    except Exception as e:
        logger.error("Email send error", extra={"error": str(e)})
        return False


async def notify_qc_complete(reviewer_email: str, report_id: str, pass_fail: bool, quality_score: int | None, error_count: int) -> None:
    status_text = "PASSED" if pass_fail else "FAILED"
    score_text = f"{quality_score}/100" if quality_score is not None else "N/A"
    html = f"<h2>QC Complete — Report Ready for Review</h2><p>Report ID: {report_id}</p><p>Result: {status_text} | Score: {score_text} | Errors: {error_count}</p><p>Log in to TF AI-QC to review.</p>"
    await _send(reviewer_email, f"[TF AI-QC] Report Ready for Review — {status_text}", html)


async def notify_revision_requested(appraiser_email: str, report_id: str, revision_notes: str) -> None:
    notes_preview = revision_notes[:200] + "..." if len(revision_notes) > 200 else revision_notes
    html = f"<h2>Revision Requested on Your Report</h2><p>Report: {report_id}</p><blockquote>{notes_preview}</blockquote><p>Log in to TF AI-QC to view the full feedback and resubmit.</p>"
    await _send(appraiser_email, "[TF AI-QC] Revision Requested — Action Required", html)


async def notify_approved(appraiser_email: str, report_id: str, quality_score: int | None) -> None:
    score_text = f"{quality_score}/100" if quality_score is not None else "N/A"
    html = f"<h2>Report Approved</h2><p>Report {report_id} has been approved. Quality Score: {score_text}</p>"
    await _send(appraiser_email, "[TF AI-QC] Report Approved", html)
