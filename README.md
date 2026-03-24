# Startup Research

Paste a company name, website, or LinkedIn page. Get a synthesized research brief in 90 seconds.

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Fill in your API keys
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## API Keys Needed
- `ANTHROPIC_API_KEY` — from console.anthropic.com
- `TAVILY_API_KEY` — from tavily.com (free tier: 1,000 searches/mo)
- `DATABASE_URL` — Supabase Postgres connection string
