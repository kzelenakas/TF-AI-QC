"""Pass 2 Quality Scorer — 0-100 score with 5 weighted sub-scorers.

Weights: Comparables 30%, Adjustments 25%, Market Analysis 20%, Narrative 15%, Reconciliation 10%.
Calls Ollama (PII-scrubbed) for narrative sub-score. Falls back to 50 if AI unavailable.

SECURITY: All text PII-scrubbed via pii_scrubber before any AI call.
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from app.services.ingest.report_data import ReportData
from app.services.privacy.pii_scrubber import scrub_report_data_narratives

logger = logging.getLogger(__name__)

WEIGHTS = {"comparables": 30, "adjustments": 25, "market_analysis": 20, "narrative": 15, "reconciliation": 10}


@dataclass
class QualityScoreResult:
    total: int
    breakdown: dict[str, int]
    flags: list[dict]
    scrubbed_narrative: str


def _score_comparables(report: ReportData) -> tuple[int, list[dict]]:
    score = 100
    flags = []
    closed = report.closed_comps
    if len(closed) < 3:
        score -= 40
        flags.append({"field": "comparables", "issue": f"Only {len(closed)} closed comparable(s)"})
    elif len(closed) >= 5:
        score = min(100, score + 5)
    if report.listing_comps:
        score -= min(len(report.listing_comps) * 8, 20)
        flags.append({"field": "listing_comps", "issue": f"{len(report.listing_comps)} active/pending listing(s) used as comparables"})
    missing_sources = sum(1 for c in closed if not c.data_source)
    if missing_sources:
        score -= missing_sources * 5
        flags.append({"field": "comp_data_source", "issue": f"{missing_sources} comparable(s) missing data source"})
    missing_cq = sum(1 for c in closed if not c.condition or not c.quality)
    if missing_cq:
        score -= missing_cq * 5
        flags.append({"field": "comp_c_q_ratings", "issue": f"{missing_cq} comparable(s) missing UAD C/Q ratings"})
    return max(0, min(100, score)), flags


def _score_adjustments(report: ReportData) -> tuple[int, list[dict]]:
    score = 100
    flags = []
    closed = report.closed_comps
    if not closed:
        return 0, [{"field": "adjustments", "issue": "No closed comparables to evaluate"}]
    high_net = [c for c in closed if c.net_adjustment_pct > 15]
    high_gross = [c for c in closed if c.gross_adjustment_pct > 25]
    if high_net:
        score -= len(high_net) * 12
        flags.append({"field": "net_adjustments", "issue": f"{len(high_net)} comp(s) exceed 15% net adjustment guideline"})
    if high_gross:
        score -= len(high_gross) * 10
        flags.append({"field": "gross_adjustments", "issue": f"{len(high_gross)} comp(s) exceed 25% gross adjustment guideline"})
    gla_adjs = []
    for comp in closed:
        if comp.gla_sqft > 0 and report.subject_gla_sqft > 0:
            diff = report.subject_gla_sqft - comp.gla_sqft
            if diff != 0 and comp.net_adjustment != 0:
                gla_adjs.append(abs(comp.net_adjustment / diff))
    if len(gla_adjs) >= 2:
        avg = sum(gla_adjs) / len(gla_adjs)
        if avg > 0:
            max_var = max(abs(x - avg) / avg * 100 for x in gla_adjs)
            if max_var > 30:
                score -= 15
                flags.append({"field": "gla_adjustment_consistency", "issue": f"GLA adjustment varies by up to {max_var:.0f}% across comparables"})
    zero_adj = sum(1 for c in closed if c.net_adjustment == 0 and c.gross_adjustment == 0 and c.sale_price > 0)
    if zero_adj >= 2:
        score -= 10
        flags.append({"field": "zero_adjustments", "issue": f"{zero_adj} comparable(s) have zero net/gross adjustments"})
    return max(0, min(100, score)), flags


def _score_market_analysis(report: ReportData) -> tuple[int, list[dict]]:
    score = 100
    flags = []
    commentary = (report.market_conditions_commentary or "").strip()
    if not commentary:
        return 0, [{"field": "market_conditions_commentary", "issue": "Market conditions commentary is absent"}]
    if len(commentary) < 100:
        score -= 35
        flags.append({"field": "market_conditions_commentary", "issue": f"Commentary is very brief ({len(commentary)} chars)"})
    elif len(commentary) < 250:
        score -= 15
    key_terms = ["supply", "demand", "absorption", "days on market", "dom", "list price", "sale price", "trend", "declining", "increasing", "stable", "inventory", "active listings", "closed sales", "median", "average", "price per", "appreciation", "depreciation"]
    found_terms = sum(1 for t in key_terms if t.lower() in commentary.lower())
    if found_terms < 2:
        score -= 20
        flags.append({"field": "market_conditions_commentary", "issue": "Commentary lacks key market analysis indicators"})
    elif found_terms >= 5:
        score = min(100, score + 5)
    if not (report.neighborhood_description or "").strip():
        score -= 10
        flags.append({"field": "neighborhood_description", "issue": "Neighborhood description is absent"})
    return max(0, min(100, score)), flags


def _score_reconciliation(report: ReportData) -> tuple[int, list[dict]]:
    score = 100
    flags = []
    recon = (report.reconciliation_text or "").strip()
    if not recon:
        return 0, [{"field": "reconciliation_text", "issue": "Reconciliation section is absent"}]
    if len(recon) < 50:
        score -= 40
        flags.append({"field": "reconciliation_text", "issue": "Reconciliation is very brief"})
    range_pats = [r"\$[\d,]+\s*(?:to|-)\s*\$[\d,]+", r"between\s+\$[\d,]+\s+and\s+\$[\d,]+", r"range\s+of\s+\$"]
    for pat in range_pats:
        if re.search(pat, recon, re.IGNORECASE):
            score -= 20
            flags.append({"field": "final_value", "issue": "Reconciliation appears to state a range rather than a point value"})
            break
    if "sales_comparison" in report.approaches_used and "sales comparison" not in recon.lower():
        score -= 10
        flags.append({"field": "reconciliation_approaches", "issue": "Sales comparison approach not mentioned in reconciliation"})
    return max(0, min(100, score)), flags


async def compute_quality_score(report: ReportData) -> QualityScoreResult:
    all_flags: list[dict] = []
    comp_score, comp_flags = _score_comparables(report)
    all_flags.extend(comp_flags)
    adj_score, adj_flags = _score_adjustments(report)
    all_flags.extend(adj_flags)
    mkt_score, mkt_flags = _score_market_analysis(report)
    all_flags.extend(mkt_flags)

    scrubbed = scrub_report_data_narratives(report)
    narr_score = 50
    try:
        from app.services.ai.ollama_client import score_narrative
        ai_result = await score_narrative(scrubbed)
        narr_score = ai_result.get("score", 50)
        all_flags.extend(ai_result.get("flags", []))
    except Exception as e:
        logger.warning("Narrative AI scoring failed", extra={"error": str(e)})
        all_flags.append({"field": "narrative", "issue": "AI narrative scoring unavailable — manual review recommended"})

    recon_score, recon_flags = _score_reconciliation(report)
    all_flags.extend(recon_flags)

    breakdown = {"comparables": comp_score, "adjustments": adj_score, "market_analysis": mkt_score, "narrative": narr_score, "reconciliation": recon_score}
    total = round(sum(breakdown[k] * WEIGHTS[k] / 100 for k in WEIGHTS))

    logger.info("Quality score computed", extra={"total": total, **{f"{k}_score": v for k, v in breakdown.items()}})

    return QualityScoreResult(total=total, breakdown=breakdown, flags=all_flags, scrubbed_narrative=scrubbed)
