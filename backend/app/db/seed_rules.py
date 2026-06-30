"""
Seed the rules table with the initial UAD / GSE / USPAP rule set.

Run with: python -m app.db.seed_rules
Or via admin CLI: python -m app.cli seed-rules

Rules are upserted — safe to re-run; existing config overrides are preserved.
"""
import logging
import sys

from app.core.database import SessionLocal
from app.models.rule import Rule, RuleCategory, RuleSeverity

logger = logging.getLogger(__name__)

INITIAL_RULES: list[dict] = [
    # UAD Format
    {"code": "UAD-001", "category": RuleCategory.uad_format, "severity": RuleSeverity.error,
     "description": "Subject property address must be fully populated",
     "detail": "UAD 3.6 requires street address, city, state, zip code in designated fields.", "config": {}},
    {"code": "UAD-002", "category": RuleCategory.uad_format, "severity": RuleSeverity.error,
     "description": "Effective date of appraisal must be present and valid",
     "detail": "Effective date must be populated and not in the future.", "config": {}},
    {"code": "UAD-003", "category": RuleCategory.uad_format, "severity": RuleSeverity.error,
     "description": "Appraiser license number and state must be populated",
     "detail": "UAD requires appraiser license/certification number and issuing state.", "config": {}},
    {"code": "UAD-004", "category": RuleCategory.uad_format, "severity": RuleSeverity.error,
     "description": "Minimum 3 comparable sales required",
     "detail": "UAD URAR requires at least 3 closed comparable sales.", "config": {"min_comps": 3}},
    {"code": "UAD-005", "category": RuleCategory.uad_format, "severity": RuleSeverity.error,
     "description": "Sales comparison grid must use UAD-standardized C/Q ratings",
     "detail": "Condition (C1-C6) and Quality (Q1-Q6) ratings must match UAD Appendix D codes.", "config": {}},
    {"code": "UAD-006", "category": RuleCategory.uad_format, "severity": RuleSeverity.warning,
     "description": "Comparable sale dates should be within 12 months of effective date",
     "detail": "Sales older than 12 months require additional explanation.", "config": {"max_months": 12}},
    {"code": "UAD-007", "category": RuleCategory.uad_format, "severity": RuleSeverity.warning,
     "description": "Comparable sale proximity should be within reasonable distance",
     "detail": "Comps beyond 1 mile (urban) or 5 miles (rural) require explanation.",
     "config": {"max_urban_miles": 1.0, "max_rural_miles": 5.0}},
    {"code": "UAD-008", "category": RuleCategory.uad_format, "severity": RuleSeverity.error,
     "description": "Indicated value by sales comparison approach must be present", "config": {}},
    {"code": "UAD-009", "category": RuleCategory.uad_format, "severity": RuleSeverity.error,
     "description": "Opinion of market value must be populated and positive", "config": {}},
    {"code": "UAD-010", "category": RuleCategory.uad_format, "severity": RuleSeverity.warning,
     "description": "Contract price vs appraised value variance requires explanation if >threshold",
     "config": {"max_pct_diff": 10}},
    # GSE
    {"code": "FNMA-001", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "Net adjustment to any comp must not exceed 15% of comp sale price",
     "detail": "Fannie Mae B4-1.3-09.", "config": {"max_net_adjustment_pct": 15}},
    {"code": "FNMA-002", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "Gross adjustments to any comp must not exceed 25% of comp sale price",
     "detail": "Fannie Mae B4-1.3-09.", "config": {"max_gross_adjustment_pct": 25}},
    {"code": "FNMA-003", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "Appraiser must comment on market conditions and supply/demand trends", "config": {}},
    {"code": "FNMA-004", "category": RuleCategory.gse, "severity": RuleSeverity.warning,
     "description": "Comparables should be arm's-length transactions", "config": {}},
    {"code": "FNMA-005", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "FEMA flood zone SFHA requires flood insurance notation", "config": {}},
    {"code": "FHLMC-001", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "Freddie Mac: reconciliation must address all applicable approaches",
     "detail": "Freddie Mac 5601.4.", "config": {}},
    {"code": "FHA-001", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "FHA: property must meet HUD Minimum Property Standards",
     "detail": "FHA 4000.1 II.D.3.", "config": {}},
    {"code": "FHA-002", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "FHA: utilities must be on and operational at time of inspection",
     "detail": "FHA 4000.1.", "config": {}},
    {"code": "VA-001", "category": RuleCategory.gse, "severity": RuleSeverity.error,
     "description": "VA: tidewater procedure must be followed if value may fall below contract price",
     "detail": "VA Ch.11.", "config": {}},
    # USPAP
    {"code": "USPAP-SR1-1", "category": RuleCategory.uspap, "severity": RuleSeverity.error,
     "description": "Certification must be signed by the appraiser",
     "detail": "USPAP SR 2-3.", "config": {}},
    {"code": "USPAP-SR1-2", "category": RuleCategory.uspap, "severity": RuleSeverity.error,
     "description": "Scope of work must be defined and sufficient for intended use",
     "detail": "USPAP SR 1-2.", "config": {}},
    {"code": "USPAP-SR1-3", "category": RuleCategory.uspap, "severity": RuleSeverity.error,
     "description": "Intended use and intended users must be identified",
     "detail": "USPAP SR 2-2(b)(ii).", "config": {}},
    {"code": "USPAP-SR1-4", "category": RuleCategory.uspap, "severity": RuleSeverity.error,
     "description": "Effective date and report date must both be present",
     "detail": "USPAP SR 2-2(b)(vi).", "config": {}},
    {"code": "USPAP-ETH-1", "category": RuleCategory.uspap, "severity": RuleSeverity.error,
     "description": "Appraiser must not accept engagement contingent on predetermined value",
     "detail": "USPAP Ethics Rule.", "config": {}},
    {"code": "USPAP-COMP-1", "category": RuleCategory.uspap, "severity": RuleSeverity.warning,
     "description": "Supervisory appraiser must sign if trainee performed inspection",
     "detail": "USPAP Competency Rule.", "config": {}},
    # Quality
    {"code": "QUAL-COMP-01", "category": RuleCategory.quality, "severity": RuleSeverity.warning,
     "description": "Comparables should be closed sales — active listings reduce reliability",
     "config": {"max_active_listings": 1}},
    {"code": "QUAL-ADJ-01", "category": RuleCategory.quality, "severity": RuleSeverity.warning,
     "description": "GLA adjustment should be consistent across all comparables",
     "config": {"max_gla_adj_variance_pct": 20}},
    {"code": "QUAL-NARR-01", "category": RuleCategory.quality, "severity": RuleSeverity.warning,
     "description": "Narrative comments should not be boilerplate or templated", "config": {}},
    {"code": "QUAL-RECON-01", "category": RuleCategory.quality, "severity": RuleSeverity.warning,
     "description": "Final value should be reconciled to a point value, not a range", "config": {}},
]


def seed_rules() -> int:
    db = SessionLocal()
    try:
        count = 0
        for rule_data in INITIAL_RULES:
            existing = db.query(Rule).filter(Rule.code == rule_data["code"]).first()
            if existing:
                existing.description = rule_data["description"]
                existing.severity = rule_data["severity"]
                existing.detail = rule_data.get("detail")
                if not existing.config:
                    existing.config = rule_data["config"]
            else:
                db.add(Rule(**rule_data))
                count += 1
        db.commit()
        logger.info(f"Seed complete: {count} new rules, {len(INITIAL_RULES) - count} updated")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    inserted = seed_rules()
    print(f"Done. {inserted} rules seeded.")
    sys.exit(0)
