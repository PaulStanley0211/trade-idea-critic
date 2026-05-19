# Trade-Idea Critic

Agentic system that critiques a trader's thesis before they take the trade. The user submits a trade idea in natural language; the system returns a structured critique covering trade mechanics, thesis stress test, cognitive-bias check, and disconfirming evidence. It never recommends buy or sell.

Coordinated through LangGraph on public market data. US, Indian, and German equities. Two deeply encoded setups: Opening Range Breakout and Support/Resistance Bounce.

## Status

In development. Four-week build. See [`PLAN.md`](PLAN.md) — the source of truth for scope, architecture, and acceptance criteria.

## Tech stack

- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui, deployed on Vercel
- **Backend:** Python 3.11+ managed with **uv**, FastAPI, LangGraph, deployed on Fly.io
- **LLM:** Claude Opus (planner, synthesizer, critic) + Claude Sonnet (specialists)
- **Database:** Postgres 16 (Neon) with SQLAlchemy async + Alembic
- **Queue:** Redis (Upstash) + RQ
- **Data:** yfinance (all markets), SEC EDGAR, NSE/BSE, DGAP/Bundesanzeiger, NewsAPI + RSS
- **Testing:** pytest + hypothesis, Vitest, Playwright
- **Observability:** loguru + OpenTelemetry + Logfire; Sentry for errors

## When you start work

Read [`PLAN.md`](PLAN.md) first. Then consult:

- `backend/app/graph.py` — compiled LangGraph and orchestration entry
- `backend/app/agents/` — node implementations per specialist
- `backend/app/models/state.py` — `CritiqueState` contract between nodes
- `backend/app/llm/client.py` — single LLM client (traced, cached, cost-capped)
- `backend/prompts/` — versioned prompt templates
- `backend/evals/` — 30 reference theses and scoring rubric
- `frontend/app/` — Next.js app routes
- `docs/review-prompt.md` — code-review prompt

## Common commands

```bash
# Backend
cd backend
uv sync --extra dev
docker compose up -d                          # local Postgres + Redis
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
uv run pytest tests/unit -q                   # unit tests
uv run pytest tests/integration -q             # integration (DB + Redis)
REC=1 uv run pytest tests/integration -q       # re-record LLM cassettes
uv run python -m evals.run                     # eval against reference theses
uv run ruff check app/ tests/
uv run mypy app/

# Frontend
cd frontend
npm install
npm run dev
npm run test                                   # vitest
npm run test:e2e                               # playwright
npm run lint
npx tsc --noEmit

# One-shot critique (debug)
cd backend
uv run python -m app.scripts.critique_once --thesis "Long AAPL 195, stop 192, target 201"
```

## Conventions

- **No Unicode emoji.** Anywhere — source, comments, commits, logs, critiques, dashboard, docs. Functional typography (arrows, plus-minus, box-drawing) is permitted when design calls for it.
- **Quality bar.** Type hints on every public function. Docstrings on modules and non-trivial functions. No dead code, no commented-out blocks, no `print` (use loguru). Functions under ~40 lines, modules under ~300. ruff and mypy zero warnings; eslint and tsc zero warnings.
- **Code review on every change.** Mechanism: Claude in IDE reviews using `docs/review-prompt.md`, then 12-hour self-review cooling-off. Verdict in PR body. Full checklist in [`PLAN.md`](PLAN.md) §4.
- **uv only on backend.** No `pip install` in scripts, Dockerfiles, or docs. Lock with `uv.lock`. Dockerfile uses `uv sync --frozen`.
- **Agent nodes are pure functions of `CritiqueState`.** Side effects only through `app/memory/` or `app/tools/`. No direct DB or HTTP calls inside a node.
- **All LLM calls go through `app/llm/client.py`** — traces, caches, enforces daily cost cap, supports cassette replay. Never import the anthropic SDK elsewhere.
- **Database access through `app/memory/` only.** Parameterized queries; no raw SQL in agent code.
- **The critic runs on every synthesizer output.** No bypass path. Unverified claims dropped or flagged.
- **Output filter blocks "buy," "sell," "recommend."** The critic rewords flagged language.
- **Prompt injection defense.** External content (filings, news, market data text) wrapped in `<source>` tags; system prompts instruct the model to treat that content as data, not instructions.
- **Cost guard.** LLM client enforces `MAX_DAILY_LLM_COST_USD` as a daily cap. Exceeded → calls fail closed.
- **API contract is the contract.** Frontend and backend evolve independently; OpenAPI schema in `backend/app/api/openapi.json` is checked into Git and consumed by the frontend.

## Required environment variables

**Backend (`.env`):**

`ANTHROPIC_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `EDGAR_USER_AGENT` (format: `"<name> <email>"`), `NEWSAPI_KEY`, `MAX_DAILY_LLM_COST_USD`, `LOG_LEVEL`, `ENVIRONMENT` (dev/staging/prod), `LLM_CACHE_DIR`, `LOGFIRE_TOKEN`, `SENTRY_DSN`.

Optional: `FINNHUB_API_KEY` (fallback market data), `SLACK_WEBHOOK_URL` (alerts).

**Frontend (`.env.local`):**

`NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SENTRY_DSN`.

See [`.env.example`](.env.example) at the repo root.
