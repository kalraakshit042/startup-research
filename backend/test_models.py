"""Tests for models.py — Pydantic validation."""
import pytest
from pydantic import ValidationError
from models import ResearchRequest


class TestResearchRequest:
    def test_valid_query(self):
        req = ResearchRequest(query="Stripe")
        assert req.query == "Stripe"

    def test_min_length_enforced(self):
        with pytest.raises(ValidationError):
            ResearchRequest(query="A")

    def test_max_length_enforced(self):
        with pytest.raises(ValidationError):
            ResearchRequest(query="x" * 501)

    def test_strips_whitespace_in_query(self):
        """Whitespace-only beyond min length should still be accepted by Pydantic."""
        req = ResearchRequest(query="  Stripe  ")
        assert req.query == "  Stripe  "  # Pydantic doesn't strip by default

    def test_two_char_minimum(self):
        req = ResearchRequest(query="AI")
        assert req.query == "AI"

    def test_url_as_query(self):
        req = ResearchRequest(query="https://stripe.com")
        assert "stripe.com" in req.query

    def test_linkedin_url_as_query(self):
        req = ResearchRequest(query="https://linkedin.com/company/stripe")
        assert "linkedin" in req.query
