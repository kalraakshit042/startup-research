import pytest


@pytest.fixture
def sample_search_results():
    """Sample Tavily search results for testing."""
    return [
        {"title": "Stripe Overview", "url": "https://stripe.com", "content": "Stripe is a technology company..."},
        {"title": "Stripe Funding", "url": "https://crunchbase.com/stripe", "content": "Stripe raised $600M..."},
        {"title": "Stripe Team", "url": "https://linkedin.com/company/stripe", "content": "Founded by Patrick and John Collison..."},
    ]


@pytest.fixture
def sample_sections():
    """Sample completed sections for testing."""
    return {
        "tldr": {"content": "Stripe builds payment infrastructure.", "order": 0},
        "story": {"content": "Founded in 2010 by the Collison brothers.", "order": 1},
        "team": {"content": "Patrick Collison (CEO), John Collison (President).", "order": 2},
    }
