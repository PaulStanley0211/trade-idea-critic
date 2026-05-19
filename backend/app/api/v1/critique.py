"""Critique endpoints (Phase 1.2 stub).

POST queues a critique; GET reads the latest state; SSE streams progress
events. In this Phase 1.2 stub, "queuing" actually fabricates a canned
response in-process. Phase 1.3 wires this to the LangGraph pipeline backed by
Postgres + Redis, after which this module's I/O contract stays identical.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

import uuid_utils
from fastapi import APIRouter, HTTPException, Response, status
from sse_starlette.sse import EventSourceResponse

from app.models.api import (
    BiasFinding,
    CritiquePending,
    CritiqueQueued,
    CritiqueRequest,
    CritiqueResponse,
    CritiqueSections,
    DisconfirmingItem,
    ParsedThesis,
    StressTestClaim,
    StructureFinding,
)

router = APIRouter(prefix="/api/v1", tags=["critique"])


# In-memory store for the W1.2 stub. Keyed by request_id (str form of UUID).
# Replaced by `app.memory.repositories.critique_repo` in W1.3.
_STUB_STORE: dict[str, dict[str, object]] = {}


def _new_request_id() -> UUID:
    """Return a fresh UUIDv7. v7 is sortable by creation time, useful for paging later."""
    return UUID(str(uuid_utils.uuid7()))


def _stub_response(request_id: UUID, raw_thesis: str, created_at: datetime) -> CritiqueResponse:
    """Build a canned `CritiqueResponse` that the frontend can render end-to-end."""
    return CritiqueResponse(
        request_id=request_id,
        status="complete",
        verdict="marginal",
        raw_thesis=raw_thesis,
        parsed_thesis=ParsedThesis(
            ticker="AAPL",
            exchange="US",
            direction="long",
            entry=195.0,
            stop=192.0,
            target=201.0,
            setup="orb",
            time_horizon="intraday",
            claims=["volume above 20-day average", "tech sector strong today"],
            raw_confidence_words=[],
        ),
        sections=CritiqueSections(
            mechanics=StructureFinding(
                rr_ratio=2.0,
                atr_14=2.5,
                stop_to_atr_multiple=1.2,
                sizing_note="Stub: sizing not evaluated.",
                verdict="Stub mechanics: R/R is acceptable; stop within ATR.",
                issues=[],
            ),
            stress_test=[
                StressTestClaim(
                    claim="volume above 20-day average",
                    verdict="unverifiable",
                    evidence=["Stub: data tool not wired in W1.2."],
                ),
            ],
            bias=[
                BiasFinding(
                    bias="recency",
                    span="(stub) tech sector strong today",
                    severity="low",
                    explanation="Stub: bias detector not wired in W1.2.",
                ),
            ],
            disconfirming=[
                DisconfirmingItem(
                    source="(stub)",
                    headline="Stub headline: disconfirming retriever not wired in W1.2.",
                    url=None,
                    relevance="ticker",
                    summary="Replaced in W3 with NewsAPI + RSS results.",
                ),
            ],
            base_rates=[],
        ),
        gap_flags=["w1.2_stub_response"],
        cost_usd=0.0,
        created_at=created_at,
        completed_at=created_at,
    )


@router.post(
    "/critique",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CritiqueQueued,
    summary="Submit a thesis for critique",
)
async def submit_critique(payload: CritiqueRequest) -> CritiqueQueued:
    """Queue a critique. Returns the `request_id` the client polls or streams."""
    request_id = _new_request_id()
    created_at = datetime.now(UTC)
    _STUB_STORE[str(request_id)] = {
        "raw_thesis": payload.thesis,
        "created_at": created_at,
        "response": _stub_response(request_id, payload.thesis, created_at),
    }
    return CritiqueQueued(request_id=request_id)


@router.get(
    "/critique/{request_id}",
    response_model=CritiqueResponse | CritiquePending,
    summary="Fetch a critique",
    responses={404: {"description": "Unknown request_id."}},
)
async def get_critique(request_id: UUID) -> CritiqueResponse | CritiquePending:
    """Return the critique body, or a `pending` envelope while work is in flight."""
    entry = _STUB_STORE.get(str(request_id))
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown request_id.")
    response = entry["response"]
    assert isinstance(response, CritiqueResponse)
    return response


@router.get(
    "/critique/{request_id}/stream",
    summary="Stream critique progress (SSE)",
    response_class=EventSourceResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "SSE stream. See docs/api/sse-events.md for event types.",
        },
        404: {"description": "Unknown request_id."},
    },
)
async def stream_critique(request_id: UUID) -> Response:
    """Emit `status`, `node_started`, `node_completed`, `final` events.

    The W1.2 stub emits a canned timeline of events spaced 200ms apart, then a
    `final` event carrying the same response that `GET /critique/{id}` returns.
    """
    entry = _STUB_STORE.get(str(request_id))
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown request_id.")
    response = entry["response"]
    assert isinstance(response, CritiqueResponse)

    async def event_stream() -> AsyncIterator[dict[str, str]]:
        nodes = [
            ("parser", "Parsing thesis..."),
            ("planner", "Dispatching specialists..."),
            ("structure_critic", "Stub mechanics done."),
            ("setup_orb", "Stub setup specialist done."),
            ("synthesizer", "Drafting critique..."),
            ("critic", "Verifying claims..."),
        ]
        yield {
            "event": "status",
            "data": json.dumps({"phase": "parsing", "message": "Parsing thesis..."}),
        }
        for node_name, summary in nodes:
            await asyncio.sleep(0.2)
            yield {"event": "node_started", "data": json.dumps({"node_name": node_name})}
            await asyncio.sleep(0.2)
            yield {
                "event": "node_completed",
                "data": json.dumps(
                    {
                        "node_name": node_name,
                        "summary": summary,
                        "partial_state_keys": [],
                    }
                ),
            }
        yield {"event": "final", "data": response.model_dump_json()}

    return EventSourceResponse(event_stream())
