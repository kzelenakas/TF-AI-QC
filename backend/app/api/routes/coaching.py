"""Coaching API Routes

GET /coaching/appraisers                          — All appraisers summary (reviewer/admin)
GET /coaching/appraisers/{appraiser_id}           — Full profile (reviewer/admin)
GET /coaching/appraisers/{appraiser_id}/recommendations — Prioritized coaching actions
GET /coaching/me                                  — Appraiser views own profile
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.auth import CurrentUser, get_current_user, require_reviewer
from app.core.database import get_db
from app.models.report import Report
from app.models.user import User, UserRole
from app.services.coaching.pattern_detector import DEFAULT_LOOKBACK_DAYS, AppraiserCoachingProfile, detect_patterns
from app.services.coaching.recommendations import build_recommendations

router = APIRouter(prefix="/coaching", tags=["coaching"])
logger = logging.getLogger(__name__)


class RulePatternOut(BaseModel):
    rule_code: str; rule_description: str; category: str; severity: str
    fire_count: int; report_count: int; total_reports: int; fire_rate_pct: float; is_recurring: bool


class QualityTrendOut(BaseModel):
    report_id: str; run_number: int; quality_score: int | None; pass_fail: bool; completed_at: str


class CoachingProfileOut(BaseModel):
    appraiser_id: str; bubble_user_id: str; total_reports: int; reports_in_window: int
    pass_rate_pct: float; avg_quality_score: float | None
    patterns: list[RulePatternOut]; quality_trend: list[QualityTrendOut]
    lookback_days: int; generated_at: str


class RecommendationOut(BaseModel):
    rule_code: str; priority: str; title: str; guidance: str; resource: str


class AppraiserSummaryOut(BaseModel):
    appraiser_id: str; bubble_user_id: str; name: str; email: str
    total_reports: int; recent_pass_rate_pct: float | None; avg_quality_score: float | None; recurring_pattern_count: int


def _profile_to_out(p: AppraiserCoachingProfile) -> CoachingProfileOut:
    return CoachingProfileOut(
        appraiser_id=p.appraiser_id, bubble_user_id=p.bubble_user_id, total_reports=p.total_reports,
        reports_in_window=p.reports_in_window, pass_rate_pct=p.pass_rate_pct, avg_quality_score=p.avg_quality_score,
        patterns=[RulePatternOut(rule_code=x.rule_code, rule_description=x.rule_description, category=x.category, severity=x.severity, fire_count=x.fire_count, report_count=x.report_count, total_reports=x.total_reports, fire_rate_pct=x.fire_rate_pct, is_recurring=x.is_recurring) for x in p.patterns],
        quality_trend=[QualityTrendOut(report_id=t.report_id, run_number=t.run_number, quality_score=t.quality_score, pass_fail=t.pass_fail, completed_at=t.completed_at) for t in p.quality_trend],
        lookback_days=p.lookback_days, generated_at=p.generated_at,
    )


@router.get("/appraisers", response_model=list[AppraiserSummaryOut])
def list_appraisers(lookback_days: int = Query(DEFAULT_LOOKBACK_DAYS, ge=7, le=365), current_user: CurrentUser = Depends(require_reviewer), db: Session = Depends(get_db)):
    appraisers = db.query(User).filter(User.role == UserRole.appraiser, User.is_active.is_(True)).order_by(User.name.asc()).all()
    summaries = []
    for a in appraisers:
        total = db.query(func.count(Report.id)).filter(Report.uploader_id == a.id).scalar() or 0
        if total == 0:
            summaries.append(AppraiserSummaryOut(appraiser_id=a.id, bubble_user_id=a.bubble_user_id, name=a.name, email=a.email, total_reports=0, recent_pass_rate_pct=None, avg_quality_score=None, recurring_pattern_count=0))
            continue
        profile = detect_patterns(a.id, db, lookback_days=lookback_days)
        summaries.append(AppraiserSummaryOut(appraiser_id=a.id, bubble_user_id=a.bubble_user_id, name=a.name, email=a.email, total_reports=total, recent_pass_rate_pct=profile.pass_rate_pct if profile.reports_in_window > 0 else None, avg_quality_score=profile.avg_quality_score, recurring_pattern_count=sum(1 for p in profile.patterns if p.is_recurring)))
    return summaries


@router.get("/appraisers/{appraiser_id}", response_model=CoachingProfileOut)
def get_appraiser_profile(appraiser_id: str, lookback_days: int = Query(DEFAULT_LOOKBACK_DAYS, ge=7, le=365), current_user: CurrentUser = Depends(require_reviewer), db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == appraiser_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appraiser not found")
    return _profile_to_out(detect_patterns(appraiser_id, db, lookback_days=lookback_days))


@router.get("/appraisers/{appraiser_id}/recommendations", response_model=list[RecommendationOut])
def get_recommendations(appraiser_id: str, lookback_days: int = Query(DEFAULT_LOOKBACK_DAYS, ge=7, le=365), current_user: CurrentUser = Depends(require_reviewer), db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == appraiser_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appraiser not found")
    profile = detect_patterns(appraiser_id, db, lookback_days=lookback_days)
    recs = build_recommendations(profile)
    return [RecommendationOut(rule_code=r.rule_code, priority=r.priority, title=r.title, guidance=r.guidance, resource=r.resource) for r in recs]


@router.get("/me", response_model=CoachingProfileOut)
def get_my_coaching_profile(lookback_days: int = Query(DEFAULT_LOOKBACK_DAYS, ge=7, le=365), current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.bubble_user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return _profile_to_out(detect_patterns(user.id, db, lookback_days=lookback_days))
