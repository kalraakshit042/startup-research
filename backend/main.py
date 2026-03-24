import json
import logging
import os
from contextlib import asynccontextmanager

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.sse import EventSourceResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from tavily import TavilyClient

from database import close_db, find_cached_report, generate_slug, get_report_by_slug, init_db, save_report
from models import ResearchRequest
from research import search_company, stream_research

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="Startup Research", lifespan=lifespan)

# Rate limiting: 1 research per hour per IP
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    retry_after = exc.detail or "3600"
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "message": "This site allows 1 search per hour. Check back soon.",
            "retry_after": int(retry_after) if str(retry_after).isdigit() else 3600,
        },
        headers={"Retry-After": str(retry_after)},
    )


# API clients — lazy init to avoid errors when env vars aren't set yet
anthropic_client = None
tavily_client = None


def get_clients():
    global anthropic_client, tavily_client
    if anthropic_client is None:
        anthropic_client = anthropic.AsyncAnthropic()
    if tavily_client is None:
        tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    return anthropic_client, tavily_client


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/research")
@limiter.limit("1/hour")
async def research(request: Request, body: ResearchRequest):
    """Generate a research brief for a company. Returns SSE stream."""
    company = body.query.strip()
    requester_ip = get_remote_address(request)
    ac, tc = get_clients()

    # Check cache first
    cached = await find_cached_report(company)
    if cached:
        logger.info(f"Cache hit for '{company}', slug={cached['slug']}")

        async def cached_stream():
            yield f"event: cached\ndata: {json.dumps({'slug': cached['slug']})}\n\n"
            # Send all sections at once
            for key, section_data in sorted(cached["sections"].items(), key=lambda x: x[1].get("order", 0)):
                yield f"event: section\ndata: {json.dumps({'key': key, 'title': section_data.get('title', key), 'content': section_data['content']})}\n\n"
            yield f"event: complete\ndata: {json.dumps({'slug': cached['slug']})}\n\n"

        return EventSourceResponse(cached_stream())

    # Fresh research
    logger.info(f"Researching '{company}' for {requester_ip}")

    async def research_stream():
        # Step 1: Search
        yield f"event: progress\ndata: {json.dumps({'message': f'Searching for {company}...'})}\n\n"

        search_results = await search_company(tc, company)
        yield f"event: progress\ndata: {json.dumps({'message': f'Found {len(search_results)} sources. Generating brief...'})}\n\n"

        # Step 2: Stream synthesis
        slug = generate_slug(company)
        final_sections = {}
        final_sources = []
        is_complete = True
        gen_time_ms = None
        search_count = len(search_results)

        async for event in stream_research(ac, company, search_results):
            if event["type"] == "section":
                final_sections[event["key"]] = {
                    "content": event["content"],
                    "title": event["title"],
                    "order": len(final_sections),
                }
                yield f"event: section\ndata: {json.dumps({'key': event['key'], 'title': event['title'], 'content': event['content']})}\n\n"

            elif event["type"] == "progress":
                yield f"event: progress\ndata: {json.dumps({'message': event['message']})}\n\n"

            elif event["type"] == "complete":
                final_sources = event.get("sources", [])
                gen_time_ms = event.get("gen_time_ms")

            elif event["type"] == "partial_complete":
                final_sections = event.get("sections", final_sections)
                final_sources = event.get("sources", [])
                is_complete = False

            elif event["type"] == "error":
                yield f"event: error\ndata: {json.dumps({'message': event['message']})}\n\n"
                return

        # Step 3: Save to DB
        try:
            saved_slug = await save_report(
                slug=slug,
                company=company,
                input_query=body.query,
                sections=final_sections,
                sources=final_sources,
                is_complete=is_complete,
                requester_ip=requester_ip,
                search_count=search_count,
                gen_time_ms=gen_time_ms,
            )
            yield f"event: complete\ndata: {json.dumps({'slug': saved_slug})}\n\n"
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            yield f"event: complete\ndata: {json.dumps({'slug': None, 'save_error': True})}\n\n"

    return EventSourceResponse(research_stream())


@app.get("/r/{slug}")
async def get_report(slug: str):
    """Fetch a saved report by slug."""
    report = await get_report_by_slug(slug)
    if report is None:
        return JSONResponse(status_code=404, content={"error": "Report not found"})
    return report
