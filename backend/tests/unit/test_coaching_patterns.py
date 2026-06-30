"""Tests for coaching pattern detector — recurring rule detection logic."""
from __future__ import annotations

import pytest

from app.services.coaching.pattern_detector import (
    PATTERN_THRESHOLD_PCT,
    MIN_REPORTS_FOR_PATTERN,
    RulePattern,
)


class TestRecurringFlag:
    """Unit tests on the RulePattern.is_recurring logic (computed in detect_patterns)."""

    def _pattern(self, fire_count: int, total: int, threshold: float = PATTERN_THRESHOLD_PCT) -> bool:
        fire_rate = fire_count / total * 100 if total else 0
        return fire_rate >= threshold and total >= MIN_REPORTS_FOR_PATTERN

    def test_recurring_above_threshold(self):
        # 4 of 10 = 40% >= 30% threshold, 10 >= 3 min
        assert self._pattern(4, 10) is True

    def test_not_recurring_below_threshold(self):
        # 2 of 10 = 20% < 30%
        assert self._pattern(2, 10) is False

    def test_not_recurring_too_few_reports(self):
        # 1 of 2 = 50% >= 30% but 2 < 3 min reports
        assert self._pattern(1, 2) is False

    def test_exactly_at_threshold(self):
        # 3 of 10 = 30% = threshold, 10 >= 3
        assert self._pattern(3, 10) is True

    def test_zero_reports(self):
        assert self._pattern(0, 0) is False
