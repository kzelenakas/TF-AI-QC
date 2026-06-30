"""Base rule infrastructure for TF AI-QC rule engine.

All compliance rules inherit BaseRule and register via @register.
Engine loads enabled rules + configs from DB, instantiates from RULE_REGISTRY.
"""
from __future__ import annotations
import abc
from dataclasses import dataclass, field
from app.services.ingest.report_data import ReportData


@dataclass
class RuleResult:
    rule_code: str
    passed: bool
    severity: str
    field_name: str
    message: str
    value_found: str = ""
    value_expected: str = ""

    def as_dict(self) -> dict:
        return {
            "rule_code": self.rule_code,
            "passed": self.passed,
            "severity": self.severity,
            "field_name": self.field_name,
            "message": self.message,
            "value_found": self.value_found,
            "value_expected": self.value_expected,
        }


RULE_REGISTRY: dict[str, type["BaseRule"]] = {}


def register(cls: type["BaseRule"]) -> type["BaseRule"]:
    RULE_REGISTRY[cls.code] = cls
    return cls


class BaseRule(abc.ABC):
    code: str
    default_severity: str = "error"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abc.abstractmethod
    def evaluate(self, report: ReportData) -> list[RuleResult]: ...

    def _fail(
        self,
        field_name: str,
        message: str,
        value_found: str = "",
        value_expected: str = "",
        severity: str | None = None,
    ) -> RuleResult:
        return RuleResult(
            rule_code=self.code,
            passed=False,
            severity=severity or self.default_severity,
            field_name=field_name,
            message=message,
            value_found=value_found,
            value_expected=value_expected,
        )

    def cfg(self, key: str, default):
        return self.config.get(key, default)
