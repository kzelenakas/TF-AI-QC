"""Bubble OMS Integration Client

Syncs report status changes back to the True Footage Bubble OMS.
Non-blocking — failures are logged but never fail the pipeline.
Only status strings and IDs are sent to Bubble (no NPI).
"""
from __future__ import annotations
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)
BUBBLE_TIMEOUT_SECONDS = 10


async def sync_report_status(report_id: str, new_status: str, quality_score: int | None = None, pass_fail: bool | None = None) -> bool:
    if not settings.bubble_data_api_url or not settings.bubble_data_api_key:
        logger.debug("Bubble sync skipped — not configured", extra={"report_id": report_id})
        return False
    payload: dict = {"qc_status": new_status}
    if quality_score is not None:
        payload["qc_quality_score"] = quality_score
    if pass_fail is not None:
        payload["qc_pass_fail"] = pass_fail
    url = f"{settings.bubble_data_api_url.rstrip('/')}/report/{report_id}"
    try:
        async with httpx.AsyncClient(timeout=BUBBLE_TIMEOUT_SECONDS) as client:
            resp = await client.patch(url, json=payload, headers={"Authorization": f"Bearer {settings.bubble_data_api_key}", "Content-Type": "application/json"})
        if resp.status_code in (200, 204):
            logger.info("Bubble OMS sync success", extra={"report_id": report_id, "status": new_status})
            return True
        logger.warning("Bubble OMS sync non-200", extra={"report_id": report_id, "http_status": resp.status_code})
        return False
    except Exception as e:
        logger.error("Bubble OMS sync failed", extra={"report_id": report_id, "error": str(e)})
        return False
