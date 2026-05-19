"""FastAPI application entry point.

Mounts the v1 router; provides a `/api/v1/health` endpoint that probes the
database, Redis, and the last successful LLM call (the last two are stubbed
until Phase 1.3 wires `app/memory/` and `app/llm/client.py`).
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from app import __version__


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """App startup and shutdown hooks. Extended in Phase 1.3 with DB/Redis init."""
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


@app.get("/api/v1/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Liveness probe. Phase 1.3 extends this with DB, Redis, and LLM checks."""
    return {"status": "ok", "version": __version__}
