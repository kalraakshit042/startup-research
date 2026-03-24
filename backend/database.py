import asyncpg
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone


pool: asyncpg.Pool | None = None


async def init_db():
    """Initialize the connection pool and create tables if needed."""
    global pool
    pool = await asyncpg.create_pool(os.environ["DATABASE_URL"], min_size=1, max_size=5)

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                slug         VARCHAR(100) UNIQUE NOT NULL,
                company      VARCHAR(255) NOT NULL,
                input_query  TEXT NOT NULL,
                sections     JSONB NOT NULL,
                sources      JSONB DEFAULT '[]',
                is_complete  BOOLEAN DEFAULT true,
                generated_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at   TIMESTAMPTZ NOT NULL,
                requester_ip INET,
                token_count  INTEGER,
                search_count INTEGER,
                gen_time_ms  INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_reports_slug ON reports(slug);
            CREATE INDEX IF NOT EXISTS idx_reports_expires ON reports(expires_at);
        """)


async def close_db():
    """Close the connection pool."""
    global pool
    if pool:
        await pool.close()


def generate_slug(company_name: str) -> str:
    """Generate a URL-safe slug: company-name-6charuuid."""
    # Normalize: lowercase, replace spaces/special chars with hyphens
    slug_base = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    slug_base = slug_base[:50]  # Cap length
    short_uuid = uuid.uuid4().hex[:6]
    return f"{slug_base}-{short_uuid}"


async def get_report_by_slug(slug: str) -> dict | None:
    """Fetch a report by slug. Returns None if not found."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM reports WHERE slug = $1", slug)
        if row is None:
            return None
        result = dict(row)
        result["id"] = str(result["id"])
        result["sections"] = json.loads(result["sections"]) if isinstance(result["sections"], str) else result["sections"]
        result["sources"] = json.loads(result["sources"]) if isinstance(result["sources"], str) else result["sources"]
        return result


async def find_cached_report(company: str) -> dict | None:
    """Find a non-expired report for the same company (cache hit)."""
    now = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM reports
               WHERE LOWER(company) = LOWER($1)
               AND expires_at > $2
               AND is_complete = true
               ORDER BY generated_at DESC LIMIT 1""",
            company, now
        )
        if row is None:
            return None
        result = dict(row)
        result["id"] = str(result["id"])
        result["sections"] = json.loads(result["sections"]) if isinstance(result["sections"], str) else result["sections"]
        result["sources"] = json.loads(result["sources"]) if isinstance(result["sources"], str) else result["sources"]
        return result


async def save_report(
    slug: str,
    company: str,
    input_query: str,
    sections: dict,
    sources: list[str],
    is_complete: bool = True,
    requester_ip: str | None = None,
    token_count: int | None = None,
    search_count: int | None = None,
    gen_time_ms: int | None = None,
) -> str:
    """Save a report and return the slug. Retries with new slug on collision."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    for attempt in range(3):
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO reports
                       (slug, company, input_query, sections, sources, is_complete,
                        expires_at, requester_ip, token_count, search_count, gen_time_ms)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
                    slug, company, input_query,
                    json.dumps(sections), json.dumps(sources),
                    is_complete, expires_at,
                    requester_ip, token_count, search_count, gen_time_ms,
                )
                return slug
        except asyncpg.UniqueViolationError:
            # Slug collision — regenerate
            slug = generate_slug(company)

    raise RuntimeError("Failed to generate unique slug after 3 attempts")
