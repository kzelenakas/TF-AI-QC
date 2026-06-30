"""USPAP Compliance Rules — SR 1, SR 2, Ethics Rule, Competency Rule."""
from __future__ import annotations
from app.services.ingest.report_data import ReportData
from app.services.rules.base_rule import BaseRule, RuleResult, register


@register
class USPAP_SR1_1Rule(BaseRule):
    code = "USPAP-SR1-1"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if not report.appraiser_signed:
            return [self._fail("appraiser_certification", "Appraiser certification is unsigned — USPAP SR 2-3 requires a signed certification in every written appraisal report.")]
        return []


@register
class USPAP_SR1_2Rule(BaseRule):
    code = "USPAP-SR1-2"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        scope = (report.scope_of_work or "").strip()
        if len(scope) < 30:
            return [self._fail("scope_of_work", f"Scope of work is {'missing' if not scope else 'insufficient'} — USPAP SR 1-2 requires scope identifying data sources, inspection type, and approaches.", value_found=f"{len(scope)} characters", value_expected="Defined scope of work")]
        return []


@register
class USPAP_SR1_3Rule(BaseRule):
    code = "USPAP-SR1-3"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        results = []
        if not (report.intended_use or "").strip():
            results.append(self._fail("intended_use", "Intended use is not identified — USPAP SR 2-2(b)(ii) requires intended use to be stated."))
        if not (report.intended_users or "").strip():
            results.append(self._fail("intended_users", "Intended user(s) not identified — USPAP SR 2-2(b)(ii) requires identification of client and intended users."))
        return results


@register
class USPAP_SR1_4Rule(BaseRule):
    code = "USPAP-SR1-4"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        results = []
        if not report.effective_date:
            results.append(self._fail("effective_date", "Effective date absent — USPAP SR 2-2(b)(vi) requires effective date to be stated."))
        if not report.report_date:
            results.append(self._fail("report_date", "Report date absent — USPAP SR 2-2(b)(vi) requires date of report to be stated."))
        return results


@register
class USPAP_ETH_1Rule(BaseRule):
    code = "USPAP-ETH-1"
    default_severity = "error"
    _PROHIBITED = ["contingent upon", "contingent on", "based on a predetermined", "predetermined value", "minimum value", "if the value", "approval of a loan", "favorable opinion", "meet the contract price", "hit the number"]
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        combined = " ".join([report.scope_of_work or "", report.intended_use or "", report.reconciliation_text or "", report.additional_comments or ""]).lower()
        found = [p for p in self._PROHIBITED if p in combined]
        if found:
            return [self._fail("ethics_prohibited_condition", f"Report contains language suggesting a prohibited assignment condition — USPAP Ethics Rule. Found: '{found[0]}'", value_found=found[0], value_expected="No prohibited conditions")]
        return []


@register
class USPAP_COMP_1Rule(BaseRule):
    code = "USPAP-COMP-1"
    default_severity = "warning"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if report.supervisory_appraiser_name and not report.supervisory_signed:
            return [self._fail("supervisory_appraiser_signature", f"Supervisory appraiser identified but not signed — USPAP Competency Rule requires supervisory co-signature when trainee performs inspection.", value_found="Named, not signed", value_expected="Supervisory signature present", severity="warning")]
        return []
