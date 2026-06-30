"""PDF Extractor — URAR PDF → ReportData

Uses pdfplumber for text extraction + regex patterns against known URAR form labels.
Accuracy is lower than XML path — rule engine treats missing PDF fields as warnings.

SECURITY: raw_text is full extracted PDF text. MUST be PII-scrubbed before AI.
"""
import io
import logging
import re

import pdfplumber

from app.services.ingest.report_data import ComparableSale, ReportData

logger = logging.getLogger(__name__)


def _after_label(text: str, label: str, max_chars: int = 120) -> str:
    m = re.search(rf"{re.escape(label)}\s*[:\.]?\s*(.{{1,{max_chars}}}?)(?:\n|$)", text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else ""


def _dollar_value(text: str, label: str) -> float:
    m = re.search(rf"{re.escape(label)}\s*[:\.]?\s*\$?\s*([\d,]+(?:\.\d{{2}})?)", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return 0.0


def _extract_date(raw: str) -> str:
    if not raw:
        return ""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw.strip())
    if m:
        return f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"
    m2 = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw.strip())
    if m2:
        return raw.strip()[:10]
    return raw.strip()


def _extract_comp_block(text: str, comp_num: int) -> ComparableSale:
    comp = ComparableSale()
    block = ""
    patterns = [
        rf"COMPARABLE\s+(?:SALE\s+)?#?\s*{comp_num}(.*?)(?:COMPARABLE\s+(?:SALE\s+)?#?\s*{comp_num + 1}|INDICATED VALUE|RECONCILIATION)",
        rf"COMP(?:ARABLE)?\s*{comp_num}(.*?)(?:COMP(?:ARABLE)?\s*{comp_num + 1}|INDICATED VALUE|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            block = m.group(1)
            break
    if not block:
        return comp

    price_m = re.search(r"(?:sale price|sales price)[:\s]*\$?\s*([\d,]+)", block, re.IGNORECASE)
    if price_m:
        comp.sale_price = float(price_m.group(1).replace(",", ""))
    gla_m = re.search(r"(?:gross liv(?:ing)? area|gla)[:\s]*([\d,]+)\s*(?:sq\.?\s*ft)?", block, re.IGNORECASE)
    if gla_m:
        comp.gla_sqft = float(gla_m.group(1).replace(",", ""))
    prox_m = re.search(r"(?:proximity|distance)[:\s]*([\d.]+)\s*(?:miles?)?", block, re.IGNORECASE)
    if prox_m:
        comp.distance_miles = float(prox_m.group(1))
    net_m = re.search(r"net\s+adj(?:ustment)?[:\s]*[+\-]?\$?\s*([\d,]+)", block, re.IGNORECASE)
    if net_m:
        comp.net_adjustment = float(net_m.group(1).replace(",", ""))
    gross_m = re.search(r"gross\s+adj(?:ustment)?[:\s]*\$?\s*([\d,]+)", block, re.IGNORECASE)
    if gross_m:
        comp.gross_adjustment = float(gross_m.group(1).replace(",", ""))
    adj_m = re.search(r"(?:adjusted|indicated)\s+(?:sale\s+)?(?:price|value)[:\s]*\$?\s*([\d,]+)", block, re.IGNORECASE)
    if adj_m:
        comp.adjusted_sale_price = float(adj_m.group(1).replace(",", ""))
    cond_m = re.search(r"\bC[1-6]\b", block)
    if cond_m:
        comp.condition = cond_m.group(0)
    qual_m = re.search(r"\bQ[1-6]\b", block)
    if qual_m:
        comp.quality = qual_m.group(0)
    yr_m = re.search(r"(?:year built|yr\.? built)[:\s]*(\d{4})", block, re.IGNORECASE)
    if yr_m:
        comp.year_built = int(yr_m.group(1))
    comp.is_closed_sale = True
    return comp


def extract_pdf(file_bytes: bytes) -> ReportData:
    rd = ReportData(file_type="pdf", form_type="1004")
    errors = rd.parse_errors
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    pages.append("")
            full_text = "\n".join(pages)
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}") from e

    rd.raw_text = full_text  # MUST be scrubbed before AI
    if not full_text.strip():
        errors.append("PARSE-PDF-001: No text extracted — may be image/scanned PDF")
        logger.warning("PDF text extraction returned empty", extra={"file_type": "pdf"})
        return rd

    try:
        addr_m = re.search(r"(?:property address|subject address)[:\s]*([^\n]{5,80})", full_text, re.IGNORECASE)
        if addr_m:
            addr_full = addr_m.group(1).strip()
            parts = [p.strip() for p in addr_full.split(",")]
            rd.subject_address = parts[0] if parts else addr_full
            if len(parts) >= 2:
                rd.subject_city = parts[1]
            if len(parts) >= 3:
                state_zip = parts[2].strip().split()
                if state_zip:
                    rd.subject_state = state_zip[0]
                if len(state_zip) > 1:
                    rd.subject_zip = state_zip[1]
        rd.subject_county = _after_label(full_text, "County", 50)
    except Exception as e:
        errors.append(f"PARSE-PDF-002: Subject error: {type(e).__name__}")

    try:
        gla_m = re.search(r"(?:above grade|gross living area)[^\d]*([\d,]+)\s*(?:sq\.?\s*ft)?", full_text, re.IGNORECASE)
        if gla_m:
            rd.subject_gla_sqft = float(gla_m.group(1).replace(",", ""))
        yr_m = re.search(r"(?:year built|actual age)[:\s]*(\d{4})", full_text, re.IGNORECASE)
        if yr_m:
            rd.subject_year_built = int(yr_m.group(1))
        cond_m = re.search(r"\bC([1-6])\b", full_text)
        if cond_m:
            rd.subject_condition = f"C{cond_m.group(1)}"
        qual_m = re.search(r"\bQ([1-6])\b", full_text)
        if qual_m:
            rd.subject_quality = f"Q{qual_m.group(1)}"
        bed_m = re.search(r"(?:bedrooms?|bdrms?)[:\s]*(\d+)", full_text, re.IGNORECASE)
        if bed_m:
            rd.subject_bedrooms = int(bed_m.group(1))
        bath_m = re.search(r"(?:bathrooms?|baths?)[:\s]*([\d.]+)", full_text, re.IGNORECASE)
        if bath_m:
            rd.subject_bathrooms = float(bath_m.group(1))
    except Exception as e:
        errors.append(f"PARSE-PDF-003: Characteristics error: {type(e).__name__}")

    try:
        rd.effective_date = _extract_date(_after_label(full_text, "Effective Date of Appraisal", 20) or _after_label(full_text, "Effective Date", 20))
        rd.report_date = _extract_date(_after_label(full_text, "Date of Report", 20) or _after_label(full_text, "Report Date", 20))
        rd.inspection_date = _extract_date(_after_label(full_text, "Date of Inspection", 20))
    except Exception as e:
        errors.append(f"PARSE-PDF-004: Date error: {type(e).__name__}")

    try:
        rd.appraiser_name = _after_label(full_text, "Appraiser Name", 60)
        rd.appraiser_license = _after_label(full_text, "State Certification #", 30) or _after_label(full_text, "State License #", 30)
        rd.appraiser_signed = bool(re.search(r"signature\s+of\s+appraiser", full_text, re.IGNORECASE))
    except Exception as e:
        errors.append(f"PARSE-PDF-005: Appraiser error: {type(e).__name__}")

    try:
        rd.lender_name = _after_label(full_text, "Lender/Client", 80) or _after_label(full_text, "Client", 80)
        rd.borrower_name = _after_label(full_text, "Borrower", 60)
    except Exception as e:
        errors.append(f"PARSE-PDF-006: Client error: {type(e).__name__}")

    try:
        price = _dollar_value(full_text, "Contract Price") or _dollar_value(full_text, "Sale Price")
        if price:
            rd.contract_price = price
    except Exception as e:
        errors.append(f"PARSE-PDF-007: Contract error: {type(e).__name__}")

    try:
        flood_m = re.search(r"flood\s+zone[:\s]*([A-Z0-9\s\(\)]{1,30}?)(?:\n|FIRM)", full_text, re.IGNORECASE)
        if flood_m:
            rd.flood_zone = flood_m.group(1).strip()
            rd.in_sfha = rd.flood_zone.upper() not in ("X", "X (UNSHADED)", "C")
        rd.flood_map_number = _after_label(full_text, "FIRM Panel Number", 30) or _after_label(full_text, "Map Number", 30)
    except Exception as e:
        errors.append(f"PARSE-PDF-008: Flood error: {type(e).__name__}")

    try:
        sc_val = _dollar_value(full_text, "Indicated Value by Sales Comparison Approach")
        if sc_val:
            rd.value_by_sales_comparison = sc_val
            rd.approaches_used.append("sales_comparison")
        cost_val = _dollar_value(full_text, "Indicated Value by Cost Approach")
        if cost_val:
            rd.value_by_cost_approach = cost_val
            rd.approaches_used.append("cost")
        income_val = _dollar_value(full_text, "Indicated Value by Income Approach")
        if income_val:
            rd.value_by_income_approach = income_val
            rd.approaches_used.append("income")
        final_m = re.search(r"(?:market value|appraised value|opinion of value)[^$\d]*\$?\s*([\d,]+)", full_text, re.IGNORECASE)
        if final_m:
            rd.final_value_opinion = float(final_m.group(1).replace(",", ""))
    except Exception as e:
        errors.append(f"PARSE-PDF-009: Value opinions error: {type(e).__name__}")

    try:
        for i in range(1, 7):
            comp = _extract_comp_block(full_text, i)
            if comp.sale_price > 0 or comp.gla_sqft > 0:
                (rd.comparables if comp.is_closed_sale else rd.listing_comps).append(comp)
    except Exception as e:
        errors.append(f"PARSE-PDF-010: Comps error: {type(e).__name__}")

    try:
        def _section(start: str, ends: list[str]) -> str:
            pat = rf"{re.escape(start)}[:\s]*(.*?)(?:{'|'.join(re.escape(e) for e in ends)}|$)"
            m = re.search(pat, full_text, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip()[:3000] if m else ""
        rd.neighborhood_description = _section("NEIGHBORHOOD DESCRIPTION", ["SITE", "IMPROVEMENTS", "MARKET CONDITIONS"])
        rd.market_conditions_commentary = _section("MARKET CONDITIONS", ["SALES COMPARISON", "RECONCILIATION", "COST APPROACH"])
        rd.reconciliation_text = _section("RECONCILIATION", ["CERTIFICATION", "APPRAISER", "SUPERVISORY"])
        rd.additional_comments = _section("ADDITIONAL COMMENTS", ["CERTIFICATION", "APPRAISER"])
        rd.scope_of_work = _after_label(full_text, "Scope of Work", 500)
        rd.intended_use = _after_label(full_text, "Intended Use", 300)
        rd.intended_users = _after_label(full_text, "Intended User", 300)
    except Exception as e:
        errors.append(f"PARSE-PDF-011: Narrative error: {type(e).__name__}")

    try:
        rd.has_signed_certification = bool(re.search(r"signature\s+of\s+appraiser", full_text, re.IGNORECASE))
        rd.prior_services_disclosed = bool(re.search(r"prior\s+services", full_text, re.IGNORECASE))
    except Exception as e:
        errors.append(f"PARSE-PDF-012: Certification error: {type(e).__name__}")

    if errors:
        logger.info("PDF extraction completed with warnings", extra={"error_count": len(errors), "file_type": "pdf"})
    return rd
