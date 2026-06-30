"""Rules Admin API Routes

GET    /rules                   — List all rules (reviewer+)
PATCH  /rules/{code}/enable    — Enable rule (admin)
PATCH  /rules/{code}/disable   — Disable rule (admin)
PATCH  /rules/{code}/config    — Update rule config thresholds (admin)
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.auth import CurrentUser, require_admin, require_reviewer
from app.core.database import get_db
from app.models.rule import Rule
from app.services.rules.engine import get_engine

router = APIRouter(prefix="/rules", tags=["rules"])
logger = logging.getLogger(__name__)


class RuleOut(BaseModel):
    id: str; code: str; category: str; severity: str; description: str; detail: str; enabled: bool; config: dict
    class Config:
        from_attributes = True


class ConfigUpdateBody(BaseModel):
    config: dict


def _rule_out(r: Rule) -> RuleOut:
    return RuleOut(id=r.id, code=r.code, category=r.category.value, severity=r.severity, description=r.description, detail=r.detail or "", enabled=r.enabled, config=r.config or {})


@router.get("", response_model=list[RuleOut])
def list_rules(current_user: CurrentUser = Depends(require_reviewer), db: Session = Depends(get_db)):
    return [_rule_out(r) for r in db.query(Rule).order_by(Rule.category, Rule.code).all()]


@router.patch("/{rule_code}/enable", response_model=RuleOut)
def enable_rule(rule_code: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.query(Rule).filter(Rule.code == rule_code).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule '{rule_code}' not found")
    r.enabled = True
    db.commit()
    db.refresh(r)
    get_engine().invalidate_cache()
    logger.info("Rule enabled", extra={"rule_code": rule_code, "admin_id": current_user.user_id})
    return _rule_out(r)


@router.patch("/{rule_code}/disable", response_model=RuleOut)
def disable_rule(rule_code: str, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.query(Rule).filter(Rule.code == rule_code).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule '{rule_code}' not found")
    r.enabled = False
    db.commit()
    db.refresh(r)
    get_engine().invalidate_cache()
    logger.info("Rule disabled", extra={"rule_code": rule_code, "admin_id": current_user.user_id})
    return _rule_out(r)


@router.patch("/{rule_code}/config", response_model=RuleOut)
def update_rule_config(rule_code: str, body: ConfigUpdateBody, current_user: CurrentUser = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.query(Rule).filter(Rule.code == rule_code).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rule '{rule_code}' not found")
    r.config = {**(r.config or {}), **body.config}
    db.commit()
    db.refresh(r)
    get_engine().invalidate_cache()
    logger.info("Rule config updated", extra={"rule_code": rule_code, "admin_id": current_user.user_id})
    return _rule_out(r)
