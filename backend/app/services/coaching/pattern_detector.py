"""Coaching Pattern Detector

Analyzes an appraiser's QC history to surface recurring deficiency patterns.
Output is PII-free — only user_id, rule_codes, counts, percentages.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.qc_result import FlagSeverity, QCFlag, QCResult
from app.models.report import Report, ReportStatus
from app.models.rule import Rule

DEFAULT_LOOKBACK_DAYS = 90
PATTERN_THRESHOLD_PCT = 30.0
MIN_REPORTS_FOR_PATTERN = 3


@dataclass
class RulePattern:
    rule_code: str
    rule_description: str
    category: str
    severity: str
    fire_count: int
    report_count: int
    total_reports: int
    fire_rate_pct: float
    is_recurring: bool


@dataclass
class QualityTrend:
    report_id: str
    run_number: int
    quality_score: int | None
    pass_fail: bool
    completed_at: str


@dataclass
class AppraiserCoachingProfile:
    appraiser_id: str
    bubble_user_id: str
    total_reports: int
    reports_in_window: int
    pass_rate_pct: float
    avg_quality_score: float | None
    patterns: list[RulePattern]
    quality_trend: list[QualityTrend]
    lookback_days: int
    generated_at: str


def _get_completed_results(appraiser_id: str, db: Session, lookback_days: int) -> list[tuple[QCResult, Report]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    return (
        db.query(QCResult, Report)
        .join(Report, QCResult.report_id == Report.id)
        .filter(
            Report.uploader_id == appraiser_id,
            Report.status.in_([ReportStatus.qc_complete, ReportStatus.approved, ReportStatus.revision_requested, ReportStatus.resubmitted]),
            QCResult.created_at >= cutoff,
        )
        .order_by(QCResult.created_at.asc())
        .all()
    )


def detect_patterns(appraiser_id: str, db: Session, lookback_days: int = DEFAULT_LOOKBACK_DAYS, threshold_pct: float = PATTERN_THRESHOLD_PCT) -> AppraiserCoachingProfile:
    from app.models.user import User
    user = db.query(User).filter(User.id == appraiser_id).first()
    empty = AppraiserCoachingProfile(appraiser_id=appraiser_id, bubble_user_id=user.bubble_user_id if user else "", total_reports=0, reports_in_window=0, pass_rate_pct=0.0, avg_quality_score=None, patterns=[], quality_trend=[], lookback_days=lookback_days, generated_at=datetime.now(timezone.utc).isoformat())
    if not user:
        return empty
    total_reports = db.query(func.count(Report.id)).filter(Report.uploader_id == appraiser_id).scalar() or 0
    empty.total_reports = total_reports
    pairs = _get_completed_results(appraiser_id, db, lookback_days)
    reports_in_window = len(pairs)
    if not pairs:
        return empty
    passed = sum(1 for qc, _ in pairs if qc.pass_fail)
    pass_rate_pct = passed / reports_in_window * 100
    scores = [qc.quality_score for qc, _ in pairs if qc.quality_score is not None]
    avg_quality_score = sum(scores) / len(scores) if scores else None
    quality_trend = [QualityTrend(report_id=report.id, run_number=qc.run_number, quality_score=qc.quality_score, pass_fail=qc.pass_fail, completed_at=qc.created_at.isoformat() if qc.created_at else "") for qc, report in pairs]
    qc_result_ids = [qc.id for qc, _ in pairs]
    rule_fire_map: dict[str, set[str]] = {}
    flag_count_map: dict[str, int] = {}
    flags = db.query(QCFlag).filter(QCFlag.qc_result_id.in_(qc_result_ids), QCFlag.severity.in_([FlagSeverity.error, FlagSeverity.warning])).all()
    for flag in flags:
        rule_code = flag.rule.code if flag.rule else f"UNKNOWN:{flag.field_name}"
        if rule_code not in rule_fire_map:
            rule_fire_map[rule_code] = set()
            flag_count_map[rule_code] = 0
        rule_fire_map[rule_code].add(flag.qc_result_id)
        flag_count_map[rule_code] += 1
    rule_meta = {r.code: r for r in db.query(Rule).filter(Rule.code.in_(list(rule_fire_map.keys()))).all()} if rule_fire_map else {}
    patterns = []
    for rule_code, result_ids in rule_fire_map.items():
        report_count = len(result_ids)
        fire_rate_pct = report_count / reports_in_window * 100
        meta = rule_meta.get(rule_code)
        patterns.append(RulePattern(rule_code=rule_code, rule_description=meta.description if meta else rule_code, category=meta.category.value if meta else "unknown", severity=meta.severity if meta else "warning", fire_count=flag_count_map[rule_code], report_count=report_count, total_reports=reports_in_window, fire_rate_pct=round(fire_rate_pct, 1), is_recurring=(fire_rate_pct >= threshold_pct and reports_in_window >= MIN_REPORTS_FOR_PATTERN)))
    patterns.sort(key=lambda p: (-int(p.is_recurring), -p.fire_rate_pct))
    return AppraiserCoachingProfile(appraiser_id=appraiser_id, bubble_user_id=user.bubble_user_id, total_reports=total_reports, reports_in_window=reports_in_window, pass_rate_pct=round(pass_rate_pct, 1), avg_quality_score=round(avg_quality_score, 1) if avg_quality_score is not None else None, patterns=patterns, quality_trend=quality_trend, lookback_days=lookback_days, generated_at=datetime.now(timezone.utc).isoformat())
