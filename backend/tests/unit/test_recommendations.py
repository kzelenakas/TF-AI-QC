"""Tests for coaching recommendation builder."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.services.coaching.pattern_detector import AppraiserCoachingProfile, RulePattern
from app.services.coaching.recommendations import Recommendation, build_recommendations


def _make_profile(patterns: list[RulePattern]) -> AppraiserCoachingProfile:
    profile = MagicMock(spec=AppraiserCoachingProfile)
    profile.patterns = patterns
    return profile


def _pattern(code: str, category: str = "uspap", is_recurring: bool = True, fire_rate: float = 50.0) -> RulePattern:
    return RulePattern(
        rule_code=code,
        rule_description=f"Test rule {code}",
        category=category,
        severity="error",
        fire_count=5,
        report_count=5,
        total_reports=10,
        fire_rate_pct=fire_rate,
        is_recurring=is_recurring,
    )


class TestBuildRecommendations:
    def test_returns_recommendations_for_known_rules(self):
        profile = _make_profile([_pattern("USPAP-SR1-1")])
        recs = build_recommendations(profile)
        assert len(recs) == 1
        assert recs[0].rule_code == "USPAP-SR1-1"
        assert recs[0].priority == "critical"

    def test_sorted_by_priority(self):
        profile = _make_profile([
            _pattern("UAD-006", category="uad_format"),   # medium
            _pattern("USPAP-ETH-1", category="uspap"),    # critical
            _pattern("FNMA-001", category="gse"),         # critical
        ])
        recs = build_recommendations(profile)
        priorities = [r.priority for r in recs]
        # All critical items must appear before medium
        critical_idx = [i for i, p in enumerate(priorities) if p == "critical"]
        medium_idx = [i for i, p in enumerate(priorities) if p == "medium"]
        if critical_idx and medium_idx:
            assert max(critical_idx) < min(medium_idx)

    def test_no_duplicates(self):
        # Same rule code twice in patterns — should appear once in recs
        profile = _make_profile([
            _pattern("USPAP-SR1-1"),
            _pattern("USPAP-SR1-1"),
        ])
        recs = build_recommendations(profile)
        codes = [r.rule_code for r in recs]
        assert len(codes) == len(set(codes))

    def test_empty_patterns_returns_empty(self):
        profile = _make_profile([])
        assert build_recommendations(profile) == []

    def test_fallback_for_unknown_rule(self):
        """Unknown rule code falls back to category guidance."""
        profile = _make_profile([_pattern("UNKNOWN-999", category="gse")])
        recs = build_recommendations(profile)
        assert len(recs) == 1
        assert recs[0].rule_code == "UNKNOWN-999"
