"""FastAPI application entry point.

Mounts the v1 router and serves `/api/v1/health`. The v1 router in
`app.api.v1.critique` currently serves a Phase 1.2 stub; Phase 1.3 wires it
to the LangGraph pipeline.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app import __version__
from app.api.v1.critique import router as critique_router
from app.models.api import HealthResponse


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """App startup and shutdown. Phase 1.3 extends this with DB and Redis pool init."""
    logger.info("trade-critic backend starting, version={}", __version__)
    yield
    logger.info("trade-critic backend stopping")


app = FastAPI(
    title="Trade-Idea Critic",
    version=__version__,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# Local frontend runs on :3000; production uses same origin so CORS is a no-op.
# Tighten the origins list before shipping to production in W1.6.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

app.include_router(critique_router)


@app.get("/api/v1/health", tags=["meta"], response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Phase 1.3 extends `checks` with real DB, Redis, last_llm states."""
    return HealthResponse(
        status="ok",
        version=__version__,
        checks={"db": "stub", "redis": "stub", "last_llm": "stub"},
    )
