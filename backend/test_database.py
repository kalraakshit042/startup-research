"""Tests for database.py — slug generation and utility functions.

Note: DB integration tests (save/fetch/cache) require a live Supabase connection
and are skipped in CI. Run with: pytest -m "not integration"
"""
import pytest
from database import generate_slug


class TestGenerateSlug:
    def test_basic_slug(self):
        slug = generate_slug("Stripe")
        assert slug.startswith("stripe-")
        # 6-char UUID suffix
        assert len(slug.split("-")[-1]) == 6

    def test_special_characters_removed(self):
        slug = generate_slug("My Cool Startup!")
        assert "!" not in slug
        assert slug.startswith("my-cool-startup-")

    def test_spaces_become_hyphens(self):
        slug = generate_slug("Open AI")
        assert slug.startswith("open-ai-")

    def test_long_name_truncated(self):
        long_name = "A" * 100
        slug = generate_slug(long_name)
        # slug_base capped at 50, plus hyphen, plus 6-char UUID
        parts = slug.rsplit("-", 1)
        assert len(parts[0]) <= 50

    def test_unique_slugs(self):
        """Two calls with same input produce different slugs (UUID suffix)."""
        slug1 = generate_slug("Stripe")
        slug2 = generate_slug("Stripe")
        assert slug1 != slug2

    def test_url_safe_characters(self):
        slug = generate_slug("Stripe (Payments)")
        # Only alphanumeric and hyphens
        base = slug.rsplit("-", 1)[0]
        assert all(c.isalnum() or c == "-" for c in base)

    def test_empty_after_normalization(self):
        """Edge case: name with only special chars."""
        slug = generate_slug("!!!")
        # Should still produce a valid slug (just the UUID part)
        assert len(slug) >= 6

    def test_leading_trailing_hyphens_stripped(self):
        slug = generate_slug("-Stripe-")
        assert not slug.startswith("--")
