"""Tests for main.py — API routes and SSE streaming.

Uses httpx + FastAPI test client. DB and external API calls are mocked.
"""
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def mock_db():
    """Mock all database functions."""
    with patch("main.init_db", new_callable=AsyncMock) as mock_init, \
         patch("main.close_db", new_callable=AsyncMock) as mock_close, \
         patch("main.find_cached_report", new_callable=AsyncMock) as mock_cache, \
         patch("main.save_report", new_callable=AsyncMock) as mock_save, \
         patch("main.get_report_by_slug", new_callable=AsyncMock) as mock_get, \
         patch("main.generate_slug", return_value="test-abc123") as mock_slug:
        mock_cache.return_value = None
        mock_save.return_value = "test-abc123"
        yield {
            "init": mock_init,
            "close": mock_close,
            "cache": mock_cache,
            "save": mock_save,
            "get": mock_get,
            "slug": mock_slug,
        }


@pytest.fixture
def mock_clients():
    """Mock Anthropic and Tavily clients."""
    with patch("main.get_clients") as mock_get:
        mock_anthropic = AsyncMock()
        mock_tavily = MagicMock()
        mock_get.return_value = (mock_anthropic, mock_tavily)
        yield {"anthropic": mock_anthropic, "tavily": mock_tavily}


@pytest.mark.asyncio
async def test_health_endpoint(mock_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_report_found(mock_db):
    mock_db["get"].return_value = {
        "id": "123",
        "slug": "stripe-abc123",
        "company": "Stripe",
        "sections": {"tldr": {"content": "Test", "order": 0}},
        "sources": [],
        "is_complete": True,
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/r/stripe-abc123")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "stripe-abc123"


@pytest.mark.asyncio
async def test_get_report_not_found(mock_db):
    mock_db["get"].return_value = None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/r/nonexistent")
        assert response.status_code == 404
        assert response.json()["error"] == "Report not found"


@pytest.mark.asyncio
async def test_research_validation_too_short(mock_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/research", json={"query": "A"})
        assert response.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_research_cache_hit(mock_db):
    mock_db["cache"].return_value = {
        "slug": "stripe-cached",
        "sections": {
            "tldr": {"content": "Cached TL;DR", "title": "TL;DR", "order": 0},
        },
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/research", json={"query": "Stripe"})
        assert response.status_code == 200
        # SSE response — check content type
        assert "text/event-stream" in response.headers.get("content-type", "")
