# Startup Research

Paste a company name. Get a synthesized research brief in 90 seconds.

**[Try it live](https://akshitkalra.com/startupresearch)**

![Startup Research](assets/screenshot.png)

---

## Example

**Input:** `Harvey AI`

![Example report for Harvey AI](assets/example-report.png)

Instead of reading 15 tabs and stitching them together manually, you get one coherent research brief with sources in ~90 seconds.

---

## Who This Is For

> Job applicants evaluating offers, founders scoping competitors, angel investors doing lightweight diligence, journalists on deadline, and potential customers wondering if a startup is legit — anyone who needs a fast, coherent view of a startup without paying for institutional research tools.

---

## The Problem

Every AI research tool on the market is built for VCs. Crunchbase, PitchBook, and Harmonic charge $10K+/year and assume you're an institutional investor running deal flow.

But the real volume of startup research isn't VCs — it's the long tail: job applicants evaluating offers, journalists on deadline, curious founders scoping competitors, angel investors doing lightweight diligence, and potential customers wondering if a startup is legit.

All the data is publicly available. The bottleneck was never access — it was synthesis. Reading 15 tabs, cross-referencing Crunchbase with LinkedIn with TechCrunch, and assembling a coherent picture takes hours.

An LLM can now do that synthesis for nearly free.

## The Solution

A two-phase pipeline: **search**, then **synthesize**.

1. **Tavily** runs 10 targeted web searches (funding, team, product, competitors, culture, news, etc.)
2. **Claude Haiku** reads all the search results and writes a structured 11-section research brief
3. Sections **stream progressively** via SSE — you see the TL;DR in seconds, not minutes
4. The report is **cached for 30 days** with a shareable URL (`/r/company-slug`)
5. **1 free search per hour** to keep costs sustainable

**The 11 sections:** TL;DR · The Story · The Team · Product · Traction & Funding · Competitive Landscape · Company Culture · Social Presence · Recent Signals · Open Questions · Sources

## Technical Decisions & Tradeoffs

| Decision | Choice | Why |
|----------|--------|-----|
| **LLM** | Claude Haiku over GPT-4 | 10x cheaper, fast enough for 90s UX, surprisingly strong at synthesis with structured input |
| **Search** | Tavily over Claude's built-in web_search | 10 targeted parallel queries with control over what gets searched; free tier (1K searches/mo) |
| **Streaming** | SSE over WebSockets | Data flows one direction (server → client). No protocol negotiation, browser-native EventSource API, sections render as they arrive |
| **Database** | Supabase (Postgres) over Firebase | JSONB column stores flexible sections without schema migrations; SQL simplicity; asyncpg connection pooling |
| **Design** | Editorial/magazine over dashboard | Target audience is general public, not terminal-loving VCs. Instrument Serif signals "read this" — deliberately unusual for an AI tool |
| **Section detection** | Markdown `## Header` regex over structured JSON | Claude writes natural prose, not JSON. Regex detects headers mid-stream for real-time section extraction |

**What I cut for v1:** User accounts (rate limit by IP instead), PDF export, report comparison, configurable section ordering, email notifications.

## Architecture

```
┌──────────┐     POST /research      ┌─────────────────┐
│ React +  │ ──────────────────────▶ │ FastAPI          │
│ Vite     │                         │                  │
│ (Vercel) │                         │ 1. Validate      │
│          │                         │ 2. Check cache   │
│          │                         │ 3. Rate limit    │
│          │     SSE stream          │                  │
│          │ ◀────────────────────── │                  │
└──────────┘                         └────────┬─────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                        ┌──────────┐   ┌──────────┐   ┌──────────┐
                        │ Tavily   │   │ Claude   │   │ Supabase │
                        │ (search) │   │ Haiku    │   │ (Postgres)│
                        │ 10 queries│   │ (stream) │   │ cache +  │
                        │ parallel │   │ 11 sections│  │ persist  │
                        └──────────┘   └──────────┘   └──────────┘

Flow:
  User types company name
    → Tavily searches 10 queries (funding, team, product, etc.)
    → Results fed to Claude Haiku with structured prompt
    → Claude streams markdown with ## section headers
    → Backend detects headers via regex, yields sections as SSE events
    → Frontend renders each section as it arrives
    → Complete report saved to Supabase with 30-day TTL + shareable slug
```

## What I Learned

- **SSE section detection was the hardest part.** Claude streams markdown token-by-token. Detecting `## Section Header` boundaries mid-stream while buffering partial content required careful regex + state management. The key insight: section boundaries naturally align with Claude's own research rhythm.

- **Claude Haiku punches above its weight at synthesis.** When you give it well-structured search results with a clear prompt template, Haiku produces research briefs that rival what Sonnet generates — at 10x lower cost. The quality bottleneck is the search results, not the model.

- **A design system (DESIGN.md) forced better decisions than ad-hoc CSS.** Defining typography, color, spacing, and component patterns upfront meant every UI decision was a lookup, not a debate. Instrument Serif was a creative risk — serifs are rare in AI tools — but it instantly differentiated the product.

- **Deploying across three services (Vercel + Railway + Supabase) has more moving parts than expected.** CORS configuration, IPv6 compatibility (Railway → Supabase requires the pooler URL), Vite basePath for subpath hosting, Vercel rewrites — each was a 15-minute puzzle that wouldn't exist with a monolithic deploy.

- **Caching is the real product optimization.** The first search for a company costs ~$0.06 and takes 90 seconds. Every subsequent view costs $0.00 and loads instantly. For popular companies, the cache hit rate makes the economics work.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite 8, Tailwind CSS 4 |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Search | Tavily API (free tier) |
| AI | Claude Haiku (`claude-haiku-4-5-20251001`) |
| Database | Supabase (PostgreSQL + asyncpg) |
| Rate Limiting | slowapi (1 request/hour per IP) |
| Deployment | Vercel (frontend), Railway (backend), Supabase (DB) |
| Design | Instrument Serif + Instrument Sans + Geist Mono |

## Setup

### Prerequisites
- Python 3.11+
- Node 18+
- API keys: [Anthropic](https://console.anthropic.com), [Tavily](https://tavily.com) (free), [Supabase](https://supabase.com) (free)

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # Fill in your API keys
uvicorn main:app --reload --port 8000

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables

```
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
FRONTEND_URL=http://localhost:5173
```

### Deployment

- **Backend:** Dockerfile included — deploy to Railway, Fly.io, or any Docker host
- **Frontend:** `npm run build` → deploy `dist/` to Vercel (configured with `base: '/startupresearch'` for subpath hosting)
- **Database:** Supabase free tier — tables auto-created on first backend startup

---

Built by [Akshit Kalra](https://akshitkalra.com)
