# Startup Research

AI-powered startup research tool. Paste a company name, get an 11-section research brief.

## Stack
- **Backend:** Python + FastAPI, Tavily (search), Claude Haiku (synthesis), Supabase (Postgres)
- **Frontend:** React 18 + Vite + Tailwind CSS
- **Model:** claude-haiku-4-5-20251001

## Environment
- Python: `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3`
- Node: `/opt/homebrew/bin/node`
- Frontend: port 5173, Backend: port 8000

## Architecture
Two-phase pipeline: Tavily searches (10 queries, free tier) → Claude Haiku streams 11-section brief with ## header detection → sections sent via SSE → persisted to Supabase.

## Design System
Always read DESIGN.md before making any visual or UI decisions.
All font choices, colors, spacing, and aesthetic direction are defined there.
Do not deviate without explicit user approval.
In QA mode, flag any code that doesn't match DESIGN.md.

## Testing
- Backend: `cd backend && python -m pytest`
- Frontend: `cd frontend && npx vitest`

## Key Files
- `backend/main.py` — FastAPI routes, SSE streaming
- `backend/research.py` — Tavily search + Claude Haiku synthesis
- `backend/database.py` — Supabase/Postgres via asyncpg
- `frontend/src/App.jsx` — State machine: HOME → LOADING → REPORT → ERROR
- `frontend/src/components/InputForm.jsx` — Search input
- `frontend/src/components/ReportView.jsx` — Streaming section renderer
- `frontend/src/components/Section.jsx` — Collapsible section card
