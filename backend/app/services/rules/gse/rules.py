"""GSE Overlay Rules — Fannie Mae B4-1, Freddie Mac 5600, FHA 4000.1, VA Ch.11."""
from __future__ import annotations
from app.services.ingest.report_data import ReportData
from app.services.rules.base_rule import BaseRule, RuleResult, register


@register
class FNMA001Rule(BaseRule):
    code = "FNMA-001"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        max_net = self.cfg("max_net_adjustment_pct", 15)
        results = []
        for i, comp in enumerate(report.comparables, 1):
            if comp.sale_price <= 0:
                continue
            pct = comp.net_adjustment_pct
            if pct > max_net:
                results.append(self._fail(f"comp_{i}_net_adjustment", f"Comp {i} net adjustment is {pct:.1f}% of sale price — exceeds Fannie Mae {max_net}% guideline (B4-1.3-09).", value_found=f"{pct:.1f}%", value_expected=f"<= {max_net}%"))
        return results


@register
class FNMA002Rule(BaseRule):
    code = "FNMA-002"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        max_gross = self.cfg("max_gross_adjustment_pct", 25)
        results = []
        for i, comp in enumerate(report.comparables, 1):
            if comp.sale_price <= 0:
                continue
            pct = comp.gross_adjustment_pct
            if pct > max_gross:
                results.append(self._fail(f"comp_{i}_gross_adjustment", f"Comp {i} gross adjustment is {pct:.1f}% — exceeds Fannie Mae {max_gross}% guideline.", value_found=f"{pct:.1f}%", value_expected=f"<= {max_gross}%"))
        return results


@register
class FNMA003Rule(BaseRule):
    code = "FNMA-003"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        commentary = (report.market_conditions_commentary or "").strip()
        if len(commentary) < 50:
            return [self._fail("market_conditions_commentary", f"Market conditions commentary is {'missing' if not commentary else 'insufficient'} — Fannie Mae requires analysis of supply/demand trends.", value_found=f"{len(commentary)} characters", value_expected=">= 50 characters of substantive market analysis")]
        return []


@register
class FNMA004Rule(BaseRule):
    code = "FNMA-004"
    default_severity = "warning"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        results = []
        for i, comp in enumerate(report.comparables, 1):
            if not comp.is_arms_length:
                results.append(self._fail(f"comp_{i}_arms_length", f"Comp {i} is a non-arm's-length transaction. Additional comparable(s) and explanation required.", value_found="Non-arm's-length", value_expected="Arm's-length transaction", severity="warning"))
        return results


@register
class FNMA005Rule(BaseRule):
    code = "FNMA-005"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if report.in_sfha and not report.flood_map_number.strip():
            return [self._fail("flood_zone", f"Property is in SFHA (Zone: {report.flood_zone or 'unknown'}) — FIRM map number must be recorded and flood insurance noted.", value_found=f"Zone: {report.flood_zone}, FIRM#: (missing)", value_expected="FIRM panel number populated")]
        return []


@register
class FHLMC001Rule(BaseRule):
    code = "FHLMC-001"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        recon = (report.reconciliation_text or "").strip()
        if len(recon) < 30:
            return [self._fail("reconciliation_text", f"Reconciliation is {'missing' if not recon else 'insufficient'} — Freddie Mac 5601.4 requires reconciliation to explain weight given to each approach.", value_found=f"{len(recon)} characters", value_expected="Substantive reconciliation commentary")]
        return []


@register
class FHA001Rule(BaseRule):
    code = "FHA-001"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        full_text = ((report.additional_comments or "") + " " + (report.reconciliation_text or "")).lower()
        mps_keywords = ["subject to", "as repaired", "roof", "foundation crack", "mold", "water intrusion", "electrical", "broken", "damaged", "peeling paint", "lead paint", "missing", "inoperable"]
        found = [kw for kw in mps_keywords if kw in full_text]
        if found and "subject to" not in full_text and "as repaired" not in full_text:
            return [self._fail("hud_mps", f"Report text suggests potential HUD MPS deficiencies ({', '.join(found[:3])}) but report is not noted as 'Subject To'. FHA 4000.1 requires conditions of value for MPS deficiencies.", value_found=f"Keywords: {', '.join(found[:3])}", value_expected="'Subject To' designation or clear MPS compliance", severity="warning")]
        return []


@register
class FHA002Rule(BaseRule):
    code = "FHA-002"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        full = ((report.scope_of_work or "") + " " + (report.additional_comments or "")).lower()
        for phrase in ["utilities not on", "utilities were not", "utilities off", "no utilities", "unable to test"]:
            if phrase in full:
                return [self._fail("fha_utilities", f"Report indicates utilities may not have been operational — FHA 4000.1 requires utilities on at inspection. Phrase: '{phrase}'", value_found=phrase, value_expected="All utilities operational")]
        return []


@register
class VA001Rule(BaseRule):
    code = "VA-001"
    default_severity = "error"
    def evaluate(self, report: ReportData) -> list[RuleResult]:
        if not report.contract_price or not report.final_value_opinion:
            return []
        if report.final_value_opinion < report.contract_price:
            full = ((report.scope_of_work or "") + " " + (report.additional_comments or "")).lower()
            if "tidewater" not in full:
                return [self._fail("va_tidewater", f"Appraised value (${report.final_value_opinion:,.0f}) is below contract price (${report.contract_price:,.0f}). VA Ch.11 requires Tidewater procedure documented in report.", value_found=f"Value ${report.final_value_opinion:,.0f} < Contract ${report.contract_price:,.0f}", value_expected="Tidewater procedure documented", severity="warning")]
        return []
