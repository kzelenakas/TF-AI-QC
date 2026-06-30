"""UAD 3.6 XML Parser — MISMO XML → ReportData

Parses Uniform Appraisal Dataset 3.6 XML (MISMO 2.6 with GSE extensions).
Parser is defensive — missing elements produce parse_errors, not crashes.

SECURITY: Never logs addresses, names, or financial data. Logs only:
file_type, element counts, parse error codes.
"""
import logging
import re
from typing import Any

from lxml import etree

from app.services.ingest.report_data import ComparableSale, ReportData

logger = logging.getLogger(__name__)

_UAD_DATE_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})$")


def _uad_date(raw: str | None) -> str:
    if not raw:
        return ""
    m = _UAD_DATE_RE.match(raw.strip())
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return raw.strip()


def _text(el: Any, path: str) -> str:
    try:
        results = el.xpath(path)
        if results:
            val = results[0]
            return (val.text or "").strip() if hasattr(val, "text") else str(val).strip()
    except Exception:
        pass
    return ""


def _float(val: str) -> float:
    try:
        return float(val.replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0


def _int(val: str) -> int:
    try:
        return int(val.strip())
    except (ValueError, AttributeError):
        return 0


def _bool_yn(val: str) -> bool:
    return val.strip().upper() in ("Y", "YES", "TRUE", "1")


def parse_xml(file_bytes: bytes) -> ReportData:
    rd = ReportData(file_type="xml")
    try:
        root = etree.fromstring(file_bytes)
    except etree.XMLSyntaxError as e:
        raise ValueError(f"XML parse failed: {e}") from e

    # Strip namespace prefixes
    for el in root.iter():
        if el.tag and el.tag.startswith("{"):
            el.tag = el.tag.split("}", 1)[1]

    errors = rd.parse_errors

    try:
        rd.form_type = _text(root, ".//FORM_IDENTIFIER") or _text(root, ".//FormIdentifier") or "1004"
    except Exception:
        errors.append("PARSE-001: Could not determine form type")

    try:
        subj = root.find(".//SUBJECT_PROPERTY") or root.find(".//SubjectProperty")
        if subj is not None:
            rd.subject_address = _text(subj, ".//StreetAddress") or _text(subj, ".//STREET_ADDRESS")
            rd.subject_city = _text(subj, ".//City") or _text(subj, ".//CITY")
            rd.subject_state = _text(subj, ".//State") or _text(subj, ".//STATE")
            rd.subject_zip = _text(subj, ".//PostalCode") or _text(subj, ".//ZIP_CODE")
            rd.subject_county = _text(subj, ".//County") or _text(subj, ".//COUNTY")
            rd.subject_legal_description = _text(subj, ".//LegalDescription") or _text(subj, ".//LEGAL_DESCRIPTION")
            rd.assessor_parcel_number = _text(subj, ".//AssessorParcelNumber") or _text(subj, ".//APN")
    except Exception as e:
        errors.append(f"PARSE-002: Subject property error: {type(e).__name__}")

    try:
        prop = root.find(".//PROPERTY") or root.find(".//Property") or root
        rd.subject_gla_sqft = _float(_text(prop, ".//GrossLivingArea") or _text(prop, ".//GROSS_LIVING_AREA"))
        rd.subject_lot_size = _text(prop, ".//LotSize") or _text(prop, ".//LOT_SIZE")
        rd.subject_year_built = _int(_text(prop, ".//YearBuilt") or _text(prop, ".//YEAR_BUILT"))
        rd.subject_condition = _text(prop, ".//Condition") or _text(prop, ".//CONDITION")
        rd.subject_quality = _text(prop, ".//Quality") or _text(prop, ".//QUALITY")
        rd.subject_bedrooms = _int(_text(prop, ".//BedroomsCount") or _text(prop, ".//BEDROOMS"))
        rd.subject_bathrooms = _float(_text(prop, ".//BathroomsCount") or _text(prop, ".//BATHROOMS"))
        rd.subject_property_type = _text(prop, ".//PropertyType") or _text(prop, ".//PROPERTY_TYPE")
    except Exception as e:
        errors.append(f"PARSE-003: Subject characteristics error: {type(e).__name__}")

    try:
        rd.effective_date = _uad_date(_text(root, ".//EffectiveDate") or _text(root, ".//EFFECTIVE_DATE"))
        rd.inspection_date = _uad_date(_text(root, ".//InspectionDate") or _text(root, ".//INSPECTION_DATE"))
        rd.report_date = _uad_date(_text(root, ".//ReportDate") or _text(root, ".//REPORT_DATE"))
    except Exception as e:
        errors.append(f"PARSE-004: Date error: {type(e).__name__}")

    try:
        app_el = root.find(".//APPRAISER") or root.find(".//Appraiser")
        if app_el is not None:
            rd.appraiser_name = _text(app_el, ".//Name") or _text(app_el, ".//NAME")
            rd.appraiser_license = _text(app_el, ".//LicenseNumber") or _text(app_el, ".//LICENSE_NUMBER")
            rd.appraiser_license_state = _text(app_el, ".//LicenseState") or _text(app_el, ".//LICENSE_STATE")
            rd.appraiser_certification_type = _text(app_el, ".//CertificationType") or _text(app_el, ".//CERT_TYPE")
            rd.appraiser_signed = bool(_text(app_el, ".//SignatureDate") or _text(app_el, ".//Signature"))
        sup_el = root.find(".//SUPERVISORY_APPRAISER") or root.find(".//SupervisoryAppraiser")
        if sup_el is not None:
            rd.supervisory_appraiser_name = _text(sup_el, ".//Name") or _text(sup_el, ".//NAME")
            rd.supervisory_appraiser_license = _text(sup_el, ".//LicenseNumber") or _text(sup_el, ".//LICENSE_NUMBER")
            rd.supervisory_signed = bool(_text(sup_el, ".//SignatureDate") or _text(sup_el, ".//Signature"))
    except Exception as e:
        errors.append(f"PARSE-005: Appraiser error: {type(e).__name__}")

    try:
        rd.client_name = _text(root, ".//ClientName") or _text(root, ".//CLIENT_NAME")
        rd.lender_name = _text(root, ".//LenderName") or _text(root, ".//LENDER_NAME")
        rd.borrower_name = _text(root, ".//BorrowerName") or _text(root, ".//BORROWER_NAME")
    except Exception as e:
        errors.append(f"PARSE-006: Client/lender error: {type(e).__name__}")

    try:
        contract_el = root.find(".//CONTRACT") or root.find(".//Contract")
        if contract_el is not None:
            price_raw = _text(contract_el, ".//SalePrice") or _text(contract_el, ".//SALE_PRICE")
            if price_raw:
                rd.contract_price = _float(price_raw)
            rd.contract_date = _uad_date(_text(contract_el, ".//ContractDate") or _text(contract_el, ".//CONTRACT_DATE"))
        purpose = (_text(root, ".//AppraisalPurpose") or _text(root, ".//APPRAISAL_PURPOSE")).upper()
        rd.is_purchase = "PURCHASE" in purpose
        rd.is_refinance = "REFIN" in purpose
    except Exception as e:
        errors.append(f"PARSE-007: Contract error: {type(e).__name__}")

    try:
        flood_el = root.find(".//FLOOD_INFORMATION") or root.find(".//FloodInformation")
        el = flood_el if flood_el is not None else root
        rd.flood_zone = _text(el, ".//FloodZone") or _text(el, ".//FLOOD_ZONE")
        rd.flood_map_number = _text(el, ".//FloodMapNumber") or _text(el, ".//FIRM_MAP_NUMBER")
        rd.flood_map_date = _uad_date(_text(el, ".//FloodMapDate") or _text(el, ".//FIRM_MAP_DATE"))
        sfha_raw = _text(el, ".//InSFHA") or _text(el, ".//SFHA_INDICATOR")
        rd.in_sfha = _bool_yn(sfha_raw) if sfha_raw else rd.flood_zone.upper() not in ("X", "X (UNSHADED)", "")
    except Exception as e:
        errors.append(f"PARSE-008: Flood error: {type(e).__name__}")

    try:
        sc_raw = _text(root, ".//SalesComparisonApproachValue") or _text(root, ".//SALES_COMPARISON_VALUE")
        if sc_raw:
            rd.value_by_sales_comparison = _float(sc_raw)
            rd.approaches_used.append("sales_comparison")
        cost_raw = _text(root, ".//CostApproachValue") or _text(root, ".//COST_APPROACH_VALUE")
        if cost_raw and _float(cost_raw) > 0:
            rd.value_by_cost_approach = _float(cost_raw)
            rd.approaches_used.append("cost")
        income_raw = _text(root, ".//IncomeApproachValue") or _text(root, ".//INCOME_APPROACH_VALUE")
        if income_raw and _float(income_raw) > 0:
            rd.value_by_income_approach = _float(income_raw)
            rd.approaches_used.append("income")
        final_raw = _text(root, ".//AppraisedValue") or _text(root, ".//APPRAISED_VALUE") or _text(root, ".//MarketValue")
        if final_raw:
            rd.final_value_opinion = _float(final_raw)
    except Exception as e:
        errors.append(f"PARSE-009: Value opinions error: {type(e).__name__}")

    try:
        comp_els = root.findall(".//COMPARABLE_SALE") or root.findall(".//ComparableSale") or root.findall(".//COMPARABLE")
        for comp_el in comp_els:
            try:
                comp = _parse_comparable(comp_el)
                (rd.comparables if comp.is_closed_sale else rd.listing_comps).append(comp)
            except Exception as ce:
                errors.append(f"PARSE-010: Comp error: {type(ce).__name__}")
    except Exception as e:
        errors.append(f"PARSE-010: Comparables section error: {type(e).__name__}")

    try:
        rd.neighborhood_description = _text(root, ".//NeighborhoodDescription") or _text(root, ".//NEIGHBORHOOD_DESCRIPTION")
        rd.market_conditions_commentary = _text(root, ".//MarketConditionsCommentary") or _text(root, ".//MARKET_CONDITIONS_COMMENTARY")
        rd.reconciliation_text = _text(root, ".//ReconciliationCommentary") or _text(root, ".//RECONCILIATION")
        rd.additional_comments = _text(root, ".//AdditionalComments") or _text(root, ".//ADDITIONAL_COMMENTS")
        rd.scope_of_work = _text(root, ".//ScopeOfWork") or _text(root, ".//SCOPE_OF_WORK")
        rd.intended_use = _text(root, ".//IntendedUse") or _text(root, ".//INTENDED_USE")
        rd.intended_users = _text(root, ".//IntendedUsers") or _text(root, ".//INTENDED_USERS")
    except Exception as e:
        errors.append(f"PARSE-011: Narrative error: {type(e).__name__}")

    try:
        cert_el = root.find(".//CERTIFICATION") or root.find(".//Certification")
        if cert_el is not None:
            rd.has_signed_certification = bool(_text(cert_el, ".//SignatureDate") or _text(cert_el, ".//SIGNATURE_DATE"))
        rd.prior_services_disclosed = _bool_yn(_text(root, ".//PriorServicesDisclosed") or "N")
    except Exception as e:
        errors.append(f"PARSE-012: Certification error: {type(e).__name__}")

    if errors:
        logger.info("XML parse completed with warnings", extra={"error_count": len(errors), "file_type": "xml"})
    return rd


def _parse_comparable(el: Any) -> ComparableSale:
    comp = ComparableSale()
    comp.address = _text(el, ".//Address") or _text(el, ".//STREET_ADDRESS")
    comp.sale_price = _float(_text(el, ".//SalePrice") or _text(el, ".//SALE_PRICE"))
    comp.sale_date = _uad_date(_text(el, ".//SaleDate") or _text(el, ".//SALE_DATE"))
    comp.distance_miles = _float(_text(el, ".//Distance") or _text(el, ".//PROXIMITY"))
    comp.gla_sqft = _float(_text(el, ".//GrossLivingArea") or _text(el, ".//GLA"))
    comp.lot_size = _text(el, ".//LotSize") or _text(el, ".//LOT_SIZE")
    comp.year_built = _int(_text(el, ".//YearBuilt") or _text(el, ".//YEAR_BUILT"))
    comp.condition = _text(el, ".//Condition") or _text(el, ".//CONDITION")
    comp.quality = _text(el, ".//Quality") or _text(el, ".//QUALITY")
    comp.net_adjustment = _float(_text(el, ".//NetAdjustment") or _text(el, ".//NET_ADJUSTMENT"))
    comp.gross_adjustment = _float(_text(el, ".//GrossAdjustment") or _text(el, ".//GROSS_ADJUSTMENT"))
    comp.adjusted_sale_price = _float(_text(el, ".//AdjustedSalePrice") or _text(el, ".//ADJUSTED_PRICE"))
    comp.data_source = _text(el, ".//DataSource") or _text(el, ".//DATA_SOURCE")
    al_raw = _text(el, ".//ArmsLength") or _text(el, ".//ARMS_LENGTH") or "Y"
    comp.is_arms_length = _bool_yn(al_raw)
    status_raw = (_text(el, ".//SaleStatus") or _text(el, ".//SALE_STATUS") or "CLOSED").upper()
    comp.is_closed_sale = status_raw not in ("ACTIVE", "PENDING", "LISTING", "ACTIVE LISTING")
    dom_raw = _text(el, ".//DaysOnMarket") or _text(el, ".//DOM")
    if dom_raw:
        comp.days_on_market = _int(dom_raw)
    return comp
