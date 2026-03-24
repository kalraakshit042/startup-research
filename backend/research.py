import anthropic
import re
import time
from tavily import TavilyClient
from typing import AsyncGenerator


# Section definitions in order
SECTIONS = [
    ("tldr", "TL;DR"),
    ("story", "The Story"),
    ("team", "The Team"),
    ("product", "Product"),
    ("traction", "Traction & Funding"),
    ("competitive", "Competitive Landscape"),
    ("culture", "Company Culture"),
    ("social", "Social Presence"),
    ("signals", "Recent Signals"),
    ("questions", "Open Questions"),
    ("sources", "Sources"),
]

SECTION_TITLES = {key: title for key, title in SECTIONS}

MAX_SEARCH_RESULTS = 30  # Cap fed to Claude to stay within context


def build_search_queries(company: str) -> list[str]:
    """Build 10 targeted search queries for a company."""
    return [
        f"{company} company overview what they do",
        f"{company} founder CEO background linkedin",
        f"{company} funding raised investors valuation",
        f"{company} product features how it works",
        f"{company} competitors market landscape",
        f"{company} company culture values glassdoor",
        f"{company} twitter linkedin social media presence",
        f"{company} recent news launches 2024 2025 2026",
        f"{company} hiring jobs growth",
        f"{company} revenue customers traction",
    ]


async def search_company(tavily_client: TavilyClient, company: str) -> list[dict]:
    """Run Tavily searches and return combined results."""
    queries = build_search_queries(company)
    all_results = []

    for query in queries:
        try:
            response = tavily_client.search(
                query=query,
                max_results=3,
                search_depth="basic",
            )
            for result in response.get("results", []):
                all_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                })
        except Exception:
            # Skip failed searches — graceful degradation
            continue

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique_results.append(r)

    return unique_results


SYSTEM_PROMPT = """You are a sharp startup analyst writing a comprehensive research brief. \
You write with the clarity of a Bloomberg analyst and the storytelling of a great journalist.

Your output MUST be structured as markdown with exactly these section headers (use ## for each):

## TL;DR
3 sentences max: what they do, current stage, why interesting.

## The Story
Origin, mission, problem being solved, why now. 2-3 paragraphs.

## The Team
Founder backgrounds, key hires, notable pedigree. Be specific about names and roles.

## Product
What they built, how it works, key differentiators.

## Traction & Funding
Funding rounds (use a markdown table: Round | Amount | Date | Lead Investors), headcount trajectory, revenue signals.

## Competitive Landscape
Who else is playing, what's the moat or wedge.

## Company Culture
Values, work style, signals from job postings and reviews. Note when data is limited.

## Social Presence
Twitter/X activity, LinkedIn following, community signals. Note when data is limited.

## Recent Signals
Last 6 months: news, product launches, hiring changes, pivots.

## Open Questions
What's unproven — the honest analyst's note. 3-5 bullet points.

## Sources
List all URLs you referenced, one per line as markdown links.

RULES:
- If you don't have enough information for a section, write "Limited information available for this section." Do NOT make things up.
- Be specific: use names, numbers, dates. Vague is useless.
- The Open Questions section is where you earn trust — be genuinely critical.
- Write in a warm but authoritative tone. Not corporate, not casual."""


def build_user_prompt(company: str, search_results: list[dict]) -> str:
    """Build the user prompt with search context."""
    context_parts = []
    for i, r in enumerate(search_results[:MAX_SEARCH_RESULTS], 1):
        context_parts.append(f"[{i}] {r['title']}\nURL: {r['url']}\n{r['content'][:500]}")

    context = "\n\n".join(context_parts)

    return f"""Research the company: {company}

Here is web research data to base your analysis on:

{context}

Write the complete 11-section research brief following the format in your instructions. \
Use the search results as your primary source. Cite URLs in the Sources section."""


# Regex to detect section headers like "## TL;DR" or "## The Team"
SECTION_HEADER_RE = re.compile(r"^## (.+)$", re.MULTILINE)


def match_section_key(header_text: str) -> str | None:
    """Match a markdown header to a section key."""
    header_lower = header_text.strip().lower()
    if not header_lower:
        return None
    for key, title in SECTIONS:
        if title.lower() == header_lower:
            return key
    # Fuzzy fallback
    for key, title in SECTIONS:
        if title.lower() in header_lower or header_lower in title.lower():
            return key
    return None


async def stream_research(
    anthropic_client: anthropic.AsyncAnthropic,
    company: str,
    search_results: list[dict],
) -> AsyncGenerator[dict, None]:
    """Stream research sections as they're generated by Claude Haiku.

    Yields dicts: {"type": "section", "key": str, "title": str, "content": str}
                  {"type": "progress", "message": str}
                  {"type": "complete", "sections": dict, "sources": list}
                  {"type": "error", "message": str}
    """
    user_prompt = build_user_prompt(company, search_results)
    start_time = time.time()

    yield {"type": "progress", "message": "Synthesizing research with AI..."}

    buffer = ""
    current_section_key = None
    current_section_title = None
    completed_sections = {}
    sources = []

    try:
        async with anthropic_client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                buffer += text

                # Check for section headers in the buffer
                while True:
                    match = SECTION_HEADER_RE.search(buffer)
                    if not match:
                        break

                    header_text = match.group(1)
                    header_start = match.start()
                    new_key = match_section_key(header_text)

                    if new_key is None:
                        # Not a recognized section — skip this match
                        break

                    # Flush the previous section
                    if current_section_key is not None:
                        section_content = buffer[:header_start].strip()
                        completed_sections[current_section_key] = {
                            "content": section_content,
                            "order": len(completed_sections),
                        }
                        yield {
                            "type": "section",
                            "key": current_section_key,
                            "title": current_section_title,
                            "content": section_content,
                        }

                    # Start new section
                    current_section_key = new_key
                    current_section_title = SECTION_TITLES.get(new_key, header_text)
                    buffer = buffer[match.end():].lstrip("\n")
                    break

            # Flush the last section
            if current_section_key is not None and buffer.strip():
                section_content = buffer.strip()
                completed_sections[current_section_key] = {
                    "content": section_content,
                    "order": len(completed_sections),
                }
                yield {
                    "type": "section",
                    "key": current_section_key,
                    "title": current_section_title,
                    "content": section_content,
                }

        # Extract sources from the sources section
        if "sources" in completed_sections:
            source_content = completed_sections["sources"]["content"]
            url_pattern = re.compile(r"https?://[^\s\)]+")
            sources = url_pattern.findall(source_content)

        gen_time_ms = int((time.time() - start_time) * 1000)

        yield {
            "type": "complete",
            "sections": completed_sections,
            "sources": sources,
            "token_count": None,  # Could extract from stream response
            "search_count": len(search_results),
            "gen_time_ms": gen_time_ms,
        }

    except Exception as e:
        # Yield whatever we have so far
        if completed_sections:
            yield {
                "type": "partial_complete",
                "sections": completed_sections,
                "sources": sources,
                "error": str(e),
            }
        else:
            yield {"type": "error", "message": f"Research generation failed: {str(e)}"}
