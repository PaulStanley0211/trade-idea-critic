"""Critique endpoints.

Phase 1.3 wires POST + GET + SSE to the real LangGraph stub (`app.graph`).
Storage is still an in-memory `_RUNS` dict so a server restart loses state;
Phase 1.3c replaces it with Postgres without changing the I/O shape.

Run lifecycle:

1. POST creates a `_RunState` and a fresh `asyncio.Queue`; schedules
   `_run_graph` as a FastAPI background task; returns `{request_id}`.
2. `_run_graph` walks `graph.astream(initial, stream_mode=["updates", "values"])`,
   pushing `PipelineEvent`s onto the run's queue and accumulating the final
   state. On completion or failure it pushes the terminal event and a `None`
   sentinel to close any active SSE subscriber.
3. SSE subscribers drain the queue; clients calling SSE after completion are
   served a single `final` (or `error`) event built from the stored result.
4. GET reads `final_response` from the store; returns 404 for unknown IDs and
   the `pending` envelope while work is in flight.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

import uuid_utils
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, status
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from app.graph import graph
from app.models.api import (
    CritiquePending,
    CritiqueQueued,
    CritiqueRequest,
    CritiqueResponse,
    Verdict,
)
from app.models.state import CritiqueState, PipelineEvent

router = APIRouter(prefix="/api/v1", tags=["critique"])

RunStatus = Literal["pending", "complete", "partial", "failed"]


@dataclass
class _RunState:
    """In-memory record of a critique run. Replaced by Postgres in Phase 1.3c."""

    request_id: UUID
    raw_thesis: str
    created_at: datetime
    queue: asyncio.Queue[PipelineEvent | None]
    events: list[PipelineEvent] = field(default_factory=list)
    status: RunStatus = "pending"
    final_response: CritiqueResponse | None = None


# Process-local store of runs. Lost on restart; in chunk B.2 we move to Postgres.
_RUNS: dict[str, _RunState] = {}


def _new_request_id() -> UUID:
    """Return a fresh UUIDv7. v7 is sortable by creation time, useful for paging later."""
    return UUID(str(uuid_utils.uuid7()))


def _now() -> datetime:
    """Tz-aware now in UTC."""
    return datetime.now(UTC)


def _verdict_from(final_state: CritiqueState) -> Verdict | None:
    """Top-line verdict comes from the setup specialist's quality band."""
    if final_state.setup_critique is None:
        return None
    return final_state.setup_critique.quality


def _build_response(final_state: CritiqueState, run: _RunState) -> CritiqueResponse:
    """Translate the terminal `CritiqueState` into the public response shape."""
    status_value: Literal["complete", "partial", "failed"] = (
        "partial" if final_state.errors or final_state.gap_flags else "complete"
    )
    return CritiqueResponse(
        request_id=final_state.request_id,
        status=status_value,
        verdict=_verdict_from(final_state),
        raw_thesis=final_state.raw_thesis,
        parsed_thesis=final_state.parsed_thesis,
        sections=final_state.final_critique,
        gap_flags=final_state.gap_flags,
        cost_usd=final_state.cost_usd,
        created_at=run.created_at,
        completed_at=_now(),
    )


async def _emit(run: _RunState, event: PipelineEvent) -> None:
    """Record an event and push it to the SSE queue (best-effort, never raises)."""
    run.events.append(event)
    try:
        await run.queue.put(event)
    except Exception as exc:
        # Queue ops are advisory; never let SSE plumbing fail the graph run.
        logger.warning("SSE queue put failed for {}: {}", run.request_id, exc)


async def _run_graph(request_id: UUID) -> None:
    """Background task: run the graph and emit events; tolerate node failures."""
    run = _RUNS[str(request_id)]
    initial = CritiqueState(
        request_id=request_id,
        raw_thesis=run.raw_thesis,
        created_at=run.created_at,
    )
    seq = 0
    try:
        await _emit(
            run,
            PipelineEvent(
                request_id=request_id,
                sequence=seq,
                event_type="status",
                payload={"phase": "parsing", "message": "Parsing thesis..."},
                created_at=_now(),
            ),
        )
        seq += 1

        final_dict: dict[str, Any] | None = None
        async for mode, chunk in graph.astream(initial, stream_mode=["updates", "values"]):
            if mode == "updates":
                for node_name, update in chunk.items():
                    await _emit(
                        run,
                        PipelineEvent(
                            request_id=request_id,
                            sequence=seq,
                            event_type="node_completed",
                            node=node_name,
                            payload={
                                "summary": f"{node_name} done (stub).",
                                "partial_state_keys": list(update.keys()) if update else [],
                            },
                            created_at=_now(),
                        ),
                    )
                    seq += 1
            elif mode == "values":
                final_dict = chunk

        if final_dict is None:
            raise RuntimeError("Graph produced no terminal state.")

        final_state = CritiqueState.model_validate(final_dict)
        response = _build_response(final_state, run)
        run.final_response = response
        run.status = response.status

        await _emit(
            run,
            PipelineEvent(
                request_id=request_id,
                sequence=seq,
                event_type="final",
                payload=json.loads(response.model_dump_json()),
                created_at=_now(),
            ),
        )
    except Exception as exc:
        # Any node failure becomes an SSE `error` event; we never raise out of the task.
        logger.exception("Graph run {} failed", request_id)
        run.status = "failed"
        await _emit(
            run,
            PipelineEvent(
                request_id=request_id,
                sequence=seq,
                event_type="error",
                payload={
                    "code": "internal",
                    "message": str(exc),
                    "recoverable": False,
                },
                created_at=_now(),
            ),
        )
    finally:
        # Sentinel that tells any active SSE subscriber the stream is finished.
        await run.queue.put(None)


@router.post(
    "/critique",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CritiqueQueued,
    summary="Submit a thesis for critique",
)
async def submit_critique(
    payload: CritiqueRequest,
    background_tasks: BackgroundTasks,
) -> CritiqueQueued:
    """Queue a critique. Returns the `request_id` the client polls or streams."""
    request_id = _new_request_id()
    created_at = _now()
    _RUNS[str(request_id)] = _RunState(
        request_id=request_id,
        raw_thesis=payload.thesis,
        created_at=created_at,
        queue=asyncio.Queue(),
    )
    background_tasks.add_task(_run_graph, request_id)
    return CritiqueQueued(request_id=request_id)


@router.get(
    "/critique/{request_id}",
    response_model=CritiqueResponse | CritiquePending,
    summary="Fetch a critique",
    responses={404: {"description": "Unknown request_id."}},
)
async def get_critique(request_id: UUID) -> CritiqueResponse | CritiquePending:
    """Return the critique body, or a `pending` envelope while work is in flight."""
    run = _RUNS.get(str(request_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Unknown request_id.")
    if run.final_response is None:
        return CritiquePending(request_id=request_id, created_at=run.created_at)
    return run.final_response


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
    """Emit `status`, `node_started`, `node_completed`, `final` (or `error`) events.

    If the run is already finished, a single `final` (or `error`) event is sent
    and the stream closes.
    """
    run = _RUNS.get(str(request_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Unknown request_id.")

    async def event_stream() -> AsyncIterator[dict[str, str]]:
        # Late subscriber: nothing to await, just send the terminal event.
        if run.status != "pending":
            terminal = next(
                (e for e in reversed(run.events) if e.event_type in {"final", "error"}),
                None,
            )
            if terminal is not None:
                yield {"event": terminal.event_type, "data": json.dumps(terminal.payload)}
            return

        while True:
            event = await run.queue.get()
            if event is None:
                return
            yield {"event": event.event_type, "data": json.dumps(event.payload)}
            if event.event_type in {"final", "error"}:
                return

    return EventSourceResponse(event_stream())
