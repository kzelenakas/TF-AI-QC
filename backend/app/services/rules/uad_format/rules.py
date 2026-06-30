"""UAD Format Rules — Pass 1 hard compliance checks.

Validates UAD 3.6 field population, C/Q format codes, required elements,
comparable date/proximity, and value opinion presence.
"""
from __future__ import annotations
import re
from datetime import date, datetime
from app.services.ingest.report_data import ReportData
from app.services.rules.base_rule import BaseRule, RuleResult, register

_C_RATINGS = {"C1", "C2", "C3", "C4", "C5", "C6"}
_Q_RATINGS = {"Q1", "Q2", "Q3", "Q4", "Q5", "Q6"}


def _parse_date(d: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(d.strip(), fmt).date()
        except (ValueError, AttributeError):
            pass
    return None


@register
class UAD001Rule(BaseRule):
    code = "UAD-001"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        missing = [f for f, v in [("street_address", report.subject_address), ("city", report.subject_city), ("state", report.subject_state), ("zip", report.subject_zip)] if not v.strip()]
        if missing:
            return [self._fail("subject_address", f"Subject address incomplete — missing: {', '.join(missing)}", value_found=report.subject_full_address or "(empty)", value_expected="Full street address, city, state, zip")]
        return []


@register
class UAD002Rule(BaseRule):
    code = "UAD-002"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if not report.effective_date:
            return [self._fail("effective_date", "Effective date of appraisal is missing")]
        eff = _parse_date(report.effective_date)
        if eff is None:
            return [self._fail("effective_date", "Effective date cannot be parsed", value_found=report.effective_date, value_expected="YYYY-MM-DD")]
        if eff > date.today():
            return [self._fail("effective_date", "Effective date is in the future", value_found=report.effective_date, value_expected=f"On or before {date.today().isoformat()}")]
        return []


@register
class UAD003Rule(BaseRule):
    code = "UAD-003"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        results = []
        if not report.appraiser_license.strip():
            results.append(self._fail("appraiser_license", "Appraiser license/certification number is missing"))
        if not report.appraiser_license_state.strip():
            results.append(self._fail("appraiser_license_state", "Appraiser license state is missing"))
        return results


@register
class UAD004Rule(BaseRule):
    code = "UAD-004"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        min_comps = self.cfg("min_comps", 3)
        closed = report.closed_comps
        if len(closed) < min_comps:
            return [self._fail("comparables", f"Only {len(closed)} closed comparable sale(s) found — minimum {min_comps} required", value_found=str(len(closed)), value_expected=f">= {min_comps}")]
        return []


@register
class UAD005Rule(BaseRule):
    code = "UAD-005"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        results = []
        if report.subject_condition and report.subject_condition.upper() not in _C_RATINGS:
            results.append(self._fail("subject_condition", f"Subject condition '{report.subject_condition}' is not a valid UAD code (C1-C6)", value_found=report.subject_condition, value_expected="C1 through C6"))
        if report.subject_quality and report.subject_quality.upper() not in _Q_RATINGS:
            results.append(self._fail("subject_quality", f"Subject quality '{report.subject_quality}' is not a valid UAD code (Q1-Q6)", value_found=report.subject_quality, value_expected="Q1 through Q6"))
        for i, comp in enumerate(report.comparables, 1):
            if comp.condition and comp.condition.upper() not in _C_RATINGS:
                results.append(self._fail(f"comp_{i}_condition", f"Comp {i} condition '{comp.condition}' is not a valid UAD code", value_found=comp.condition, value_expected="C1-C6"))
            if comp.quality and comp.quality.upper() not in _Q_RATINGS:
                results.append(self._fail(f"comp_{i}_quality", f"Comp {i} quality '{comp.quality}' is not a valid UAD code", value_found=comp.quality, value_expected="Q1-Q6"))
        return results


@register
class UAD006Rule(BaseRule):
    code = "UAD-006"
    default_severity = "warning"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        max_months = self.cfg("max_months", 12)
        eff = _parse_date(report.effective_date)
        if not eff:
            return []
        results = []
        for i, comp in enumerate(report.comparables, 1):
            sale_dt = _parse_date(comp.sale_date)
            if not sale_dt:
                continue
            months_diff = (eff.year - sale_dt.year) * 12 + (eff.month - sale_dt.month)
            if months_diff > max_months:
                results.append(self._fail(f"comp_{i}_sale_date", f"Comp {i} sale date is {months_diff} months before effective date — exceeds {max_months}-month guideline. Additional explanation required.", value_found=comp.sale_date, value_expected=f"Within {max_months} months of {report.effective_date}", severity="warning"))
        return results


@register
class UAD007Rule(BaseRule):
    code = "UAD-007"
    default_severity = "warning"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        max_urban = self.cfg("max_urban_miles", 1.0)
        max_rural = self.cfg("max_rural_miles", 5.0)
        is_rural = "rural" in (report.neighborhood_description or "").lower()
        threshold = max_rural if is_rural else max_urban
        results = []
        for i, comp in enumerate(report.comparables, 1):
            if comp.distance_miles > 0 and comp.distance_miles > threshold:
                results.append(self._fail(f"comp_{i}_proximity", f"Comp {i} is {comp.distance_miles:.1f} miles away — exceeds {'rural' if is_rural else 'urban'} guideline of {threshold} miles.", value_found=f"{comp.distance_miles:.1f} miles", value_expected=f"<= {threshold} miles", severity="warning"))
        return results


@register
class UAD008Rule(BaseRule):
    code = "UAD-008"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if report.value_by_sales_comparison is None or report.value_by_sales_comparison <= 0:
            return [self._fail("value_by_sales_comparison", "Indicated value by sales comparison approach is missing or zero")]
        return []


@register
class UAD009Rule(BaseRule):
    code = "UAD-009"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if report.final_value_opinion is None or report.final_value_opinion <= 0:
            return [self._fail("final_value_opinion", "Final opinion of market value is missing or zero", value_found=str(report.final_value_opinion), value_expected="Positive dollar amount")]
        return []


@register
class UAD010Rule(BaseRule):
    code = "UAD-010"
    default_severity = "warning"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if not report.contract_price or not report.final_value_opinion:
            return []
        max_pct = self.cfg("max_pct_diff", 10)
        diff_pct = abs(report.contract_price - report.final_value_opinion) / report.contract_price * 100
        if diff_pct > max_pct:
            return [self._fail("contract_vs_appraised_value", f"Contract price and appraised value differ by {diff_pct:.1f}% — exceeds {max_pct}% threshold. Narrative explanation required.", value_found=f"Contract: ${report.contract_price:,.0f} / Value: ${report.final_value_opinion:,.0f} ({diff_pct:.1f}% diff)", value_expected=f"Variance <= {max_pct}% or narrative explanation", severity="warning")]
        return []
