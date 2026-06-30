"""Tests for server-side file validation (magic bytes)."""
from __future__ import annotations

import pytest

from app.services.qc_service import MAX_FILE_SIZE_BYTES, validate_file


XML_BYTES = b"<?xml version=\"1.0\" encoding=\"UTF-8\"?><root></root>"
PDF_BYTES = b"%PDF-1.4 fake pdf content"
INVALID_BYTES = b"\x89PNG\r\n\x1a\n fake png"


class TestValidateFile:
    def test_valid_xml_accepted(self):
        file_type = validate_file(XML_BYTES, "report.xml")
        assert file_type == "xml"

    def test_valid_pdf_accepted(self):
        file_type = validate_file(PDF_BYTES, "report.pdf")
        assert file_type == "pdf"

    def test_empty_file_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            validate_file(b"", "report.xml")

    def test_oversized_file_rejected(self):
        big = b"<?xml" + b"x" * (MAX_FILE_SIZE_BYTES + 1)
        with pytest.raises(ValueError, match="maximum size"):
            validate_file(big, "report.xml")

    def test_png_rejected(self):
        with pytest.raises(ValueError, match="Unsupported"):
            validate_file(INVALID_BYTES, "report.png")

    def test_extension_spoofing_rejected(self):
        """PNG bytes with .xml extension must be rejected — magic bytes win."""
        with pytest.raises(ValueError, match="Unsupported"):
            validate_file(INVALID_BYTES, "report.xml")
