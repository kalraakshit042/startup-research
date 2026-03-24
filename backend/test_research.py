"""Tests for research.py — search query generation, section matching, and search dedup."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from research import (
    build_search_queries,
    match_section_key,
    search_company,
    build_user_prompt,
    SECTIONS,
    SECTION_TITLES,
    MAX_SEARCH_RESULTS,
)


class TestBuildSearchQueries:
    def test_returns_10_queries(self):
        queries = build_search_queries("Stripe")
        assert len(queries) == 10

    def test_each_query_contains_company_name(self):
        queries = build_search_queries("OpenAI")
        for q in queries:
            assert "OpenAI" in q

    def test_queries_cover_key_topics(self):
        queries = build_search_queries("Acme")
        topics_found = {"funding", "product", "competitor", "culture", "news"}
        combined = " ".join(queries).lower()
        for topic in topics_found:
            assert topic in combined


class TestMatchSectionKey:
    def test_exact_match(self):
        assert match_section_key("TL;DR") == "tldr"
        assert match_section_key("The Story") == "story"
        assert match_section_key("The Team") == "team"
        assert match_section_key("Product") == "product"
        assert match_section_key("Traction & Funding") == "traction"
        assert match_section_key("Competitive Landscape") == "competitive"
        assert match_section_key("Company Culture") == "culture"
        assert match_section_key("Social Presence") == "social"
        assert match_section_key("Recent Signals") == "signals"
        assert match_section_key("Open Questions") == "questions"
        assert match_section_key("Sources") == "sources"

    def test_case_insensitive(self):
        assert match_section_key("tl;dr") == "tldr"
        assert match_section_key("THE STORY") == "story"
        assert match_section_key("the team") == "team"

    def test_fuzzy_match(self):
        assert match_section_key("The Team Members") == "team"
        assert match_section_key("Product Overview") == "product"

    def test_no_match_returns_none(self):
        assert match_section_key("Random Header") is None
        assert match_section_key("") is None

    def test_whitespace_handling(self):
        assert match_section_key("  TL;DR  ") == "tldr"
        assert match_section_key("\tThe Story\n") == "story"


class TestSearchCompany:
    @pytest.mark.asyncio
    async def test_deduplicates_by_url(self):
        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value={
            "results": [
                {"title": "Stripe", "url": "https://stripe.com", "content": "Payment infra"},
                {"title": "Stripe Again", "url": "https://stripe.com", "content": "Same URL"},
            ]
        })
        results = await search_company(mock_client, "Stripe")
        urls = [r["url"] for r in results]
        assert urls.count("https://stripe.com") == 1

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_search_failure(self):
        mock_client = MagicMock()
        call_count = 0

        def side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 5:
                raise Exception("API Error")
            return {"results": [{"title": "Result", "url": f"https://example.com/{call_count}", "content": "data"}]}

        mock_client.search = MagicMock(side_effect=side_effect)
        results = await search_company(mock_client, "Stripe")
        # 5 failed, 5 succeeded with 1 result each
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_all_queries_fail_returns_empty(self):
        mock_client = MagicMock()
        mock_client.search = MagicMock(side_effect=Exception("API Down"))
        results = await search_company(mock_client, "Stripe")
        assert results == []

    @pytest.mark.asyncio
    async def test_empty_results_handled(self):
        mock_client = MagicMock()
        mock_client.search = MagicMock(return_value={"results": []})
        results = await search_company(mock_client, "Stripe")
        assert results == []


class TestBuildUserPrompt:
    def test_includes_company_name(self):
        prompt = build_user_prompt("Stripe", [])
        assert "Stripe" in prompt

    def test_includes_search_results(self):
        results = [{"title": "Test", "url": "https://example.com", "content": "Content here"}]
        prompt = build_user_prompt("Stripe", results)
        assert "https://example.com" in prompt
        assert "Content here" in prompt

    def test_caps_at_max_results(self):
        results = [{"title": f"Result {i}", "url": f"https://example.com/{i}", "content": f"Content {i}"} for i in range(50)]
        prompt = build_user_prompt("Stripe", results)
        # Should only include MAX_SEARCH_RESULTS
        assert f"[{MAX_SEARCH_RESULTS}]" in prompt
        assert f"[{MAX_SEARCH_RESULTS + 1}]" not in prompt

    def test_truncates_long_content(self):
        results = [{"title": "Long", "url": "https://example.com", "content": "x" * 1000}]
        prompt = build_user_prompt("Stripe", results)
        # Content should be capped at 500 chars
        assert "x" * 501 not in prompt


class TestSectionsConsistency:
    def test_all_sections_have_titles(self):
        for key, title in SECTIONS:
            assert title, f"Section {key} has no title"
            assert key in SECTION_TITLES

    def test_section_count(self):
        assert len(SECTIONS) == 11
