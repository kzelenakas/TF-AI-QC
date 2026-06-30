"""Tests for PII scrubber — ensures NPI is stripped before AI calls."""
from __future__ import annotations

import pytest

from app.services.privacy.pii_scrubber import scrub_text


class TestScrubText:
    def test_scrubs_person_name(self):
        result = scrub_text("The borrower John Smith purchased the property.")
        assert "John Smith" not in result
        assert "[PERSON]" in result

    def test_scrubs_street_address(self):
        result = scrub_text("Subject property is located at 123 Main Street, Anytown, CA 90210.")
        assert "123 Main Street" not in result
        assert "[ADDRESS]" in result

    def test_scrubs_ssn(self):
        result = scrub_text("Borrower SSN: 123-45-6789")
        assert "123-45-6789" not in result
        assert "[REDACTED]" in result

    def test_scrubs_loan_number(self):
        result = scrub_text("Loan number: 1234567890")
        assert "[REDACTED]" in result

    def test_preserves_non_pii_text(self):
        text = "The subject property is a single-family residence with good condition."
        result = scrub_text(text)
        # Non-PII structural content should remain
        assert "single-family" in result
        assert "good condition" in result

    def test_empty_string(self):
        assert scrub_text("") == ""

    def test_none_returns_empty(self):
        assert scrub_text(None) == ""
