"""
PII Scrubber — strips GLBA-protected NPI before text reaches Ollama or any external AI.

Replaces: names → [PERSON], addresses → [ADDRESS], SSNs/loan numbers → [REDACTED],
dollar amounts → [VALUE], phones → [PHONE], emails → [EMAIL], APNs → [PARCEL].

MANDATORY: Call scrub() on all narrative text before passing to score_narrative().
This is a hard GLBA requirement.

Usage:
    from app.services.privacy.pii_scrubber import scrub
    clean_text = scrub(raw_narrative)
    result = await score_narrative(clean_text)
"""
import re

_DOLLAR = re.compile(r"\$[\d,]+(?:\.\d{2})?")
_PHONE = re.compile(r"(?<!\d)(?:\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})(?!\d)")
_EMAIL = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_SSN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")
_LOAN_NUMBER = re.compile(r"\b(?:loan\s*#?\s*|case\s*#?\s*|fha\s*case\s*#?\s*)[\d\-]+\b", re.IGNORECASE)
_APN = re.compile(r"\b(?:apn|parcel|assessor'?s?\s+parcel|pin)\s*#?\s*[\d\-]+\b", re.IGNORECASE)
_STREET_ADDRESS = re.compile(
    r"\b\d+\s+[A-Za-z0-9\s]{2,40}(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|"
    r"Road|Rd|Lane|Ln|Court|Ct|Circle|Cir|Way|Place|Pl|Terrace|Ter|Trail|Trl|"
    r"Highway|Hwy|Parkway|Pkwy|Suite|Ste|Unit|Apt|#)\b\.?",
    re.IGNORECASE,
)
_PO_BOX = re.compile(r"\bP\.?O\.?\s+Box\s+\d+\b", re.IGNORECASE)
_NAME_PATTERN = re.compile(
    r"\b(?:borrower|appraiser|client|owner|lender|prepared\s+by|signed\s+by)"
    r"[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,3})\b",
    re.IGNORECASE,
)
_MLS = re.compile(r"\b(?:mls|listing)\s*#?\s*[\w\d\-]+\b", re.IGNORECASE)


def scrub(text: str) -> str:
    """Strip PII from appraisal narrative text. Returns sanitized string safe for Ollama."""
    if not text:
        return ""
    text = _SSN.sub("[REDACTED]", text)
    text = _LOAN_NUMBER.sub("[REDACTED]", text)
    text = _APN.sub("[PARCEL]", text)
    text = _EMAIL.sub("[EMAIL]", text)
    text = _PHONE.sub("[PHONE]", text)
    text = _DOLLAR.sub("[VALUE]", text)
    text = _MLS.sub("[MLS]", text)
    text = _PO_BOX.sub("[ADDRESS]", text)
    text = _STREET_ADDRESS.sub("[ADDRESS]", text)
    text = _NAME_PATTERN.sub(lambda m: m.group(0).replace(m.group(1), "[PERSON]"), text)
    return text.strip()


def scrub_report_data_narratives(report_data) -> str:
    """Extract and scrub all narratives from a ReportData object. Safe for AI scoring."""
    raw = report_data.narratives_for_ai()
    return scrub(raw)
