"""Coaching Recommendations

Maps recurring rule patterns to actionable coaching guidance.
"""
from __future__ import annotations
from dataclasses import dataclass
from app.services.coaching.pattern_detector import AppraiserCoachingProfile


@dataclass
class Recommendation:
    rule_code: str
    priority: str
    title: str
    guidance: str
    resource: str = ""


_RULE_GUIDANCE: dict[str, dict] = {
    "UAD-001": {"priority": "critical", "title": "Incomplete Subject Property Address", "guidance": "Verify all address fields are populated before submission. The UAD field mapping requires street, city, state, and zip as separate elements. Check the XML output before uploading.", "resource": "UAD Appendix D, Field 1.01–1.04"},
    "UAD-002": {"priority": "critical", "title": "Effective Date Missing or Invalid", "guidance": "Effective date must be populated, in CCYYMMDD format in the XML, and must not be a future date. Confirm the date of inspection equals the effective date unless a retrospective/prospective value is intended.", "resource": "USPAP SR 2-2(b)(vi); UAD Appendix D Field 3.01"},
    "UAD-003": {"priority": "critical", "title": "Appraiser License Not Populated", "guidance": "License number and license state are required fields. Confirm the appraiser's license information is entered correctly in the form software and exports to the XML.", "resource": "UAD Appendix D Fields 11.01–11.03"},
    "UAD-004": {"priority": "high", "title": "Insufficient Closed Comparable Sales", "guidance": "A minimum of three closed comparable sales is required. Active listings and pending sales can supplement but cannot replace closed sales. If the market lacks sufficient closed comps, disclose the extended search parameters.", "resource": "Fannie Mae B4-1.3-08"},
    "UAD-005": {"priority": "high", "title": "Invalid UAD Condition/Quality Ratings", "guidance": "Condition (C1–C6) and Quality (Q1–Q6) codes must use the UAD-standardized format exactly. Common errors: using 'Average' instead of 'Q3', or free-text descriptions in UAD fields.", "resource": "UAD Appendix D, Condition and Quality Definitions"},
    "UAD-006": {"priority": "medium", "title": "Stale Comparable Sales Dates", "guidance": "Comparable sales beyond 12 months require explicit justification in the addenda explaining why more recent sales were not available and how the time adjustment supports the use of older sales.", "resource": "Fannie Mae B4-1.3-08; Freddie Mac 5601.2"},
    "UAD-007": {"priority": "medium", "title": "Comparable Proximity Exceeds Guidelines", "guidance": "Urban comparables should generally be within 1 mile; rural within 5 miles. When extended searches are necessary, explain the competitive market area boundaries.", "resource": "Fannie Mae B4-1.3-08"},
    "UAD-010": {"priority": "medium", "title": "Contract/Appraised Value Variance", "guidance": "When the appraised value differs from the contract price by more than 10%, provide a clear narrative explanation in the addenda. Avoid appearing to 'hit' the contract price without independent support.", "resource": "USPAP SR 1-5(b); Fannie Mae B4-1.3-04"},
    "FNMA-001": {"priority": "critical", "title": "Net Adjustment Exceeds 15% Guideline", "guidance": "When net adjustments exceed 15%, the appraiser must provide additional justification. Net adjustment percentage is |net adj| / sale price.", "resource": "Fannie Mae B4-1.3-09"},
    "FNMA-002": {"priority": "critical", "title": "Gross Adjustment Exceeds 25% Guideline", "guidance": "Gross adjustments over 25% indicate the comparable may not be a market peer. Review comp selection criteria.", "resource": "Fannie Mae B4-1.3-09"},
    "FNMA-003": {"priority": "high", "title": "Insufficient Market Conditions Commentary", "guidance": "The market conditions section must reflect current dynamics with specific data: supply levels, absorption rates, list-to-sale ratios, price trends. Pull actual MLS data and cite it.", "resource": "Fannie Mae B4-1.3-03; Form 1004MC"},
    "FNMA-005": {"priority": "high", "title": "SFHA Flood Zone — FIRM Number Missing", "guidance": "For FEMA Special Flood Hazard Areas, the FIRM panel number, flood zone designation, and flood insurance requirement must all be documented.", "resource": "Fannie Mae B4-1.4-07"},
    "FHLMC-001": {"priority": "high", "title": "Insufficient Reconciliation", "guidance": "Reconciliation must explain the weight given to each approach. A one-sentence reconciliation is not sufficient.", "resource": "Freddie Mac 5601.4; USPAP SR 2-2(b)(viii)"},
    "FHA-001": {"priority": "high", "title": "HUD MPS Deficiencies Not Properly Noted", "guidance": "FHA requires property conditions affecting safety, soundness, or security be noted as conditions of value. Never describe a deficiency without noting it as a condition of value on an FHA appraisal.", "resource": "HUD 4000.1 II.D.3.b"},
    "FHA-002": {"priority": "critical", "title": "FHA Utilities Not Operational", "guidance": "FHA requires all utilities on and operational at time of inspection. If utilities are off, complete 'subject to' utilities being turned on.", "resource": "HUD 4000.1 II.D.3.b(iii)"},
    "VA-001": {"priority": "high", "title": "VA Tidewater Procedure Not Documented", "guidance": "When value may come in below contract price, Tidewater must be initiated before completion. Failure to follow Tidewater is a compliance violation.", "resource": "VA Lenders Handbook Ch.11, Section 4"},
    "USPAP-SR1-1": {"priority": "critical", "title": "Unsigned Certification", "guidance": "Every appraisal report must contain the appraiser's signed certification per USPAP SR 2-3. This is a bright-line USPAP violation.", "resource": "USPAP SR 2-3"},
    "USPAP-SR1-2": {"priority": "critical", "title": "Scope of Work Insufficient", "guidance": "Scope of work must identify the type and extent of data collection, inspection type, and approaches considered.", "resource": "USPAP SR 1-2(f); SCOPE OF WORK RULE"},
    "USPAP-SR1-3": {"priority": "critical", "title": "Intended Use/Users Not Identified", "guidance": "The client and intended users must be identified. The intended use must be stated explicitly.", "resource": "USPAP SR 2-2(b)(ii)"},
    "USPAP-ETH-1": {"priority": "critical", "title": "Potential Ethics Rule Violation", "guidance": "Report text contains language suggesting the value may be contingent or predetermined. Review immediately. USPAP prohibits contingent fees.", "resource": "USPAP Ethics Rule, Management Section"},
    "USPAP-COMP-1": {"priority": "high", "title": "Supervisory Appraiser Signature Missing", "guidance": "When a trainee performs the inspection, the supervisory appraiser must co-sign.", "resource": "USPAP Competency Rule"},
}

_CATEGORY_GUIDANCE: dict[str, dict] = {
    "uad_format": {"priority": "medium", "title": "UAD Format Compliance Issue", "guidance": "Review UAD Appendix D for correct field formatting and allowable values.", "resource": "UAD Appendix D"},
    "gse": {"priority": "high", "title": "GSE Overlay Non-Compliance", "guidance": "Review the applicable GSE selling guide section.", "resource": "Fannie Mae Selling Guide B4-1"},
    "uspap": {"priority": "critical", "title": "USPAP Compliance Issue", "guidance": "USPAP compliance is non-negotiable. Review the applicable Standards Rule.", "resource": "USPAP Standards Rules 1 and 2"},
    "quality": {"priority": "medium", "title": "Report Quality Issue", "guidance": "Review the quality scoring breakdown for specific improvement areas.", "resource": ""},
}


def build_recommendations(profile: AppraiserCoachingProfile) -> list[Recommendation]:
    recs: list[Recommendation] = []
    seen: set[str] = set()
    for pattern in profile.patterns:
        if pattern.rule_code in seen:
            continue
        seen.add(pattern.rule_code)
        d = _RULE_GUIDANCE.get(pattern.rule_code) or _CATEGORY_GUIDANCE.get(pattern.category, _CATEGORY_GUIDANCE["quality"])
        recs.append(Recommendation(rule_code=pattern.rule_code, priority=d["priority"], title=d["title"], guidance=d["guidance"], resource=d.get("resource", "")))
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recs.sort(key=lambda r: priority_order.get(r.priority, 4))
    return recs
