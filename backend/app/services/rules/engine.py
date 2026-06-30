"""TF AI-QC Rule Engine — two-pass QC evaluation.

Pass 1 — Hard Compliance: UAD, GSE, USPAP rules from DB.
Pass 2 — Quality Scoring: 5 sub-scorers, Ollama narrative, 0-100 score.

Rules loaded from DB on first use (5-min TTL cache).
Call engine.invalidate_cache() after admin rule changes.

SECURITY: Only report_id, counts, scores logged — no PII.
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from app.services.ingest.report_data import ReportData
from app.services.rules.base_rule import RULE_REGISTRY, BaseRule, RuleResult
from app.services.rules.quality_scorer import QualityScoreResult, compute_quality_score

import app.services.rules.uad_format.rules  # noqa: F401
import app.services.rules.gse.rules         # noqa: F401
import app.services.rules.uspap.rules       # noqa: F401

logger = logging.getLogger(__name__)


@dataclass
class EngineResult:
    pass1_passed: bool
    pass1_error_flags: list[RuleResult]
    pass1_warning_flags: list[RuleResult]
    quality_score: int
    score_breakdown: dict[str, int]
    quality_flags: list[dict]
    all_rule_flags: list[RuleResult] = field(default_factory=list)
    rules_evaluated: int = 0
    engine_duration_ms: float = 0.0

    def to_raw_flags_jsonb(self) -> dict:
        return {
            "pass1_passed": self.pass1_passed,
            "pass1_errors": [f.as_dict() for f in self.pass1_error_flags],
            "pass1_warnings": [f.as_dict() for f in self.pass1_warning_flags],
            "quality_score": self.quality_score,
            "score_breakdown": self.score_breakdown,
            "quality_flags": self.quality_flags,
            "rules_evaluated": self.rules_evaluated,
            "engine_duration_ms": self.engine_duration_ms,
        }


class RuleEngine:
    def __init__(self):
        self._cached_rules: list[tuple[BaseRule, str]] | None = None
        self._cache_ts: float = 0.0
        self._cache_ttl_seconds: float = 300.0

    def invalidate_cache(self) -> None:
        self._cached_rules = None
        logger.info("Rule engine cache invalidated")

    def _load_rules(self, db: Session) -> list[tuple[BaseRule, str]]:
        from app.models.rule import Rule
        now = time.monotonic()
        if self._cached_rules is not None and (now - self._cache_ts) < self._cache_ttl_seconds:
            return self._cached_rules
        db_rules = db.query(Rule).filter(Rule.enabled.is_(True)).all()
        loaded = []
        missing_impl = []
        for db_rule in db_rules:
            impl_cls = RULE_REGISTRY.get(db_rule.code)
            if impl_cls is None:
                missing_impl.append(db_rule.code)
                continue
            loaded.append((impl_cls(config=db_rule.config or {}), db_rule.severity))
        if missing_impl:
            logger.warning("DB rules missing implementation", extra={"codes": missing_impl})
        logger.info("Rules loaded", extra={"total": len(db_rules), "loaded": len(loaded)})
        self._cached_rules = loaded
        self._cache_ts = now
        return loaded

    async def evaluate(self, report: ReportData, db: Session) -> EngineResult:
        start = time.monotonic()
        rules = self._load_rules(db)
        error_flags: list[RuleResult] = []
        warning_flags: list[RuleResult] = []
        for rule_instance, db_severity in rules:
            try:
                for r in rule_instance.evaluate(report):
                    if not r.passed:
                        (error_flags if r.severity == "error" or db_severity == "error" else warning_flags).append(r)
            except Exception as e:
                logger.error("Rule evaluation exception", extra={"rule_code": rule_instance.code, "error": str(e)})
        pass1_passed = len(error_flags) == 0
        quality_result = await compute_quality_score(report)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info("Engine evaluation complete", extra={"pass1_passed": pass1_passed, "errors": len(error_flags), "warnings": len(warning_flags), "quality_score": quality_result.total, "duration_ms": round(duration_ms, 1)})
        return EngineResult(
            pass1_passed=pass1_passed,
            pass1_error_flags=error_flags,
            pass1_warning_flags=warning_flags,
            quality_score=quality_result.total,
            score_breakdown=quality_result.breakdown,
            quality_flags=quality_result.flags,
            all_rule_flags=error_flags + warning_flags,
            rules_evaluated=len(rules),
            engine_duration_ms=round(duration_ms, 1),
        )


_engine_instance: RuleEngine | None = None


def get_engine() -> RuleEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RuleEngine()
    return _engine_instance
