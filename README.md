# Remix 🔀

**Feed it a campaign. Get it everywhere.**

An agentic tool that takes an existing advertising campaign and generates strategic creative declinations across formats, audiences, and platforms. Built with LangGraph multi-agent architecture.

## Architecture

```
[Campaign Brief]
       │
       ▼
┌──────────────────┐
│ Campaign Analyzer │  ← Decomposes into creative building blocks
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  Remix Planner   │  ← Plans declinations based on user choices
└──────────────────┘
       │
       ▼ (parallel fan-out)
┌──────────────────┐
│ Creative Writer  │  ← Generates each declination
└──────────────────┘
       │
       ▼
┌──────────────────┐
│ Quality Checker  │  ← Verifies consistency with original
└──────────────────┘
       │
       ▼
[Validated Remixes]
```

## Stack

- **Backend**: Python, FastAPI, LangGraph, Claude API
- **Frontend**: React + Vite
- **LLM**: Claude Sonnet (via langchain-anthropic)

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /` — Health check
- `GET /formats` — List available remix formats
- `POST /analyze` — Analyze a campaign brief
- `POST /remix` — Full remix pipeline (analyze → plan → write → check)
- `POST /remix/stream` — Same, with SSE streaming

## Author

Kevin Begranger — Creative Technologist
