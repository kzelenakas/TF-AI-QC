"""Internal / Cron Routes — protected by X-Internal-Secret header.

POST /internal/health-check        — Verify DB + R2 + Ollama
POST /internal/retry-stuck-reports — Reset reports stuck in qc_running
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.report import Report, ReportStatus

router = APIRouter(prefix="/internal", tags=["internal"])
logger = logging.getLogger(__name__)
STUCK_THRESHOLD_MINUTES = 15


def verify_internal_secret(x_internal_secret: str = Header(...)):
    if not settings.internal_cron_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Internal cron not configured")
    if x_internal_secret != settings.internal_cron_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal secret")


class HealthCheckResult(BaseModel):
    db: str; r2: str; ollama: str; overall: str


class RetryResult(BaseModel):
    stuck_count: int; retried: list[str]; message: str


@router.post("/health-check", response_model=HealthCheckResult)
async def health_check(_: None = Depends(verify_internal_secret), db: Session = Depends(get_db)):
    results: dict[str, str] = {}
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        results["db"] = "ok"
    except Exception as e:
        results["db"] = f"error: {str(e)[:100]}"
    try:
        from app.core.storage import _get_r2_client
        _get_r2_client().list_buckets()
        results["r2"] = "ok"
    except Exception as e:
        results["r2"] = f"error: {str(e)[:100]}"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_base_url.replace('/v1', '')}/api/tags")
        results["ollama"] = "ok" if resp.status_code == 200 else f"http_{resp.status_code}"
    except Exception as e:
        results["ollama"] = f"unreachable: {str(e)[:80]}"
    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    logger.info("Health check", extra={"results": results, "overall": overall})
    return HealthCheckResult(db=results["db"], r2=results["r2"], ollama=results["ollama"], overall=overall)


@router.post("/retry-stuck-reports", response_model=RetryResult)
async def retry_stuck_reports(_: None = Depends(verify_internal_secret), db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STUCK_THRESHOLD_MINUTES)
    stuck = db.query(Report).filter(Report.status == ReportStatus.qc_running, Report.updated_at < cutoff).all()
    retried_ids = []
    for report in stuck:
        report.status = ReportStatus.submitted
        retried_ids.append(report.id)
        logger.warning("Resetting stuck report", extra={"report_id": report.id})
    if retried_ids:
        db.commit()
    return RetryResult(stuck_count=len(retried_ids), retried=retried_ids, message=f"Reset {len(retried_ids)} stuck report(s).")
