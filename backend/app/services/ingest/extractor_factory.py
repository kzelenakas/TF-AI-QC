"""Extractor Factory — detect file type by magic bytes, dispatch to correct parser.

SECURITY: File type validated by magic bytes (not filename/extension).
Rejects all non-XML / non-PDF files with ValueError.
"""
import logging

from app.services.ingest.report_data import ReportData
from app.services.ingest.xml_parser import parse_xml
from app.services.ingest.pdf_extractor import extract_pdf

logger = logging.getLogger(__name__)

_PDF_MAGIC = b"%PDF"
_INSPECT_BYTES = 512


def detect_file_type(file_bytes: bytes) -> str:
    """Detect file type by magic bytes. Returns 'pdf' or 'xml'. Raises ValueError if unsupported."""
    if not file_bytes:
        raise ValueError("Empty file")
    header = file_bytes[:_INSPECT_BYTES].lstrip()
    if header.startswith(_PDF_MAGIC):
        return "pdf"
    if (
        header.startswith(b"<?xml")
        or b"<?xml" in header[:200]
        or b"VALUATION" in header[:200]
        or b"MISMO" in header[:200]
    ):
        return "xml"
    logger.warning(
        "Unsupported file type rejected",
        extra={"file_size": len(file_bytes), "header_hex": header[:16].hex()},
    )
    raise ValueError("Unsupported file type. Only UAD 3.6 XML and PDF appraisal reports are accepted.")


def extract(file_bytes: bytes) -> tuple[ReportData, str]:
    """Detect file type and parse into ReportData. Returns (ReportData, file_type_str)."""
    file_type = detect_file_type(file_bytes)
    logger.info("Starting report extraction", extra={"file_type": file_type, "file_size": len(file_bytes)})
    rd = parse_xml(file_bytes) if file_type == "xml" else extract_pdf(file_bytes)
    logger.info(
        "Extraction complete",
        extra={"file_type": file_type, "form_type": rd.form_type, "comp_count": len(rd.comparables), "parse_error_count": len(rd.parse_errors)},
    )
    return rd, file_type
