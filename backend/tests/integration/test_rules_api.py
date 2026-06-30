"""Integration tests for the rules admin API."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.models.rule import Rule, RuleCategory, RuleSeverity


def _seed_rule(db_session, code: str = "TEST-001") -> Rule:
    rule = Rule(
        code=code,
        category=RuleCategory.uad_format,
        severity=RuleSeverity.error,
        description="Test rule",
        detail="Test detail",
        enabled=True,
        config={},
    )
    db_session.add(rule)
    db_session.commit()
    return rule


class TestListRules:
    def test_reviewer_can_list(self, client_reviewer, db_session):
        _seed_rule(db_session)
        resp = client_reviewer.get("/rules")
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) >= 1
        assert rules[0]["code"] == "TEST-001"

    def test_appraiser_blocked(self, client_appraiser):
        resp = client_appraiser.get("/rules")
        assert resp.status_code == 403


class TestToggleRules:
    def test_admin_can_disable(self, client_admin, db_session):
        _seed_rule(db_session)
        with patch("app.api.routes.rules.get_engine") as mock_engine:
            mock_engine.return_value.invalidate_cache = lambda: None
            resp = client_admin.patch("/rules/TEST-001/disable")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_admin_can_enable(self, client_admin, db_session):
        rule = _seed_rule(db_session)
        rule.enabled = False
        db_session.commit()
        with patch("app.api.routes.rules.get_engine") as mock_engine:
            mock_engine.return_value.invalidate_cache = lambda: None
            resp = client_admin.patch("/rules/TEST-001/enable")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_reviewer_blocked_from_toggle(self, client_reviewer, db_session):
        _seed_rule(db_session)
        resp = client_reviewer.patch("/rules/TEST-001/disable")
        assert resp.status_code == 403

    def test_unknown_rule_404(self, client_admin):
        with patch("app.api.routes.rules.get_engine") as mock_engine:
            mock_engine.return_value.invalidate_cache = lambda: None
            resp = client_admin.patch("/rules/DOES-NOT-EXIST/enable")
        assert resp.status_code == 404


class TestUpdateRuleConfig:
    def test_admin_can_update_config(self, client_admin, db_session):
        _seed_rule(db_session)
        with patch("app.api.routes.rules.get_engine") as mock_engine:
            mock_engine.return_value.invalidate_cache = lambda: None
            resp = client_admin.patch("/rules/TEST-001/config", json={"config": {"max_net_adjustment_pct": 20}})
        assert resp.status_code == 200
        assert resp.json()["config"]["max_net_adjustment_pct"] == 20
