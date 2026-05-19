# Trade-Idea Critic

An agentic system that critiques a trader's thesis before they take the trade. Submit a trade idea in natural language; the system returns a structured critique covering trade mechanics, thesis stress test, cognitive-bias check, and disconfirming evidence. It characterizes the setup as strong, marginal, or weak — and never recommends buy or sell.

Coordinated through LangGraph on public market data. Covers US, Indian, and German equities, with two deeply encoded setups: Opening Range Breakout and Support/Resistance Bounce.

**Status:** in development (greenfield). See [`PLAN.md`](PLAN.md) for the source-of-truth scope, architecture, and acceptance criteria, and [`CLAUDE.md`](CLAUDE.md) for working conventions.

## Stack

- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui, deployed on Vercel.
- **Backend:** Python 3.11+ managed with `uv`, FastAPI, LangGraph, deployed on Fly.io.
- **LLM:** Claude Opus (planner, synthesizer, critic) + Claude Sonnet (specialists).
- **Data:** Postgres 16 (Neon), Redis (Upstash) + RQ, yfinance, SEC EDGAR, NSE/BSE, DGAP/Bundesanzeiger, NewsAPI.
- **Observability:** loguru + OpenTelemetry + Logfire; Sentry for errors.

## Quick start (local)

```bash
# Backend
cd backend
uv sync --extra dev
docker compose up -d
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# Frontend (in another shell)
cd frontend
npm install
npm run dev
```

Copy `.env.example` to `backend/.env` and `frontend/.env.local` and fill in the values before running.

## License

MIT. See [`LICENSE`](LICENSE).
