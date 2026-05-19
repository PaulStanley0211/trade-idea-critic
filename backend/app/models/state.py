"""`CritiqueState` - the contract every LangGraph node operates on.

Each node is a pure function `CritiqueState -> dict[str, Any]` that returns a
**partial** update merged into state by LangGraph. Nodes never mutate state in
place. Side effects (DB, HTTP) go through `app.memory` and `app.tools`.

This module also defines `PipelineEvent`, the canonical shape persisted to
`critique_events` and replayed onto the SSE stream.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.api import (
    BaseRateFinding,
    BiasFinding,
    CritiqueSections,
    DisconfirmingItem,
    ParsedThesis,
    SetupCritique,
    StressTestClaim,
    StructureFinding,
)

NodeName = Literal[
    "parser",
    "planner",
    "structure_critic",
    "stress_tester",
    "bias_detector",
    "disconfirming_retriever",
    "setup_specialist",
    "base_rate_evaluator",
    "synthesizer",
    "critic",
    "output_filter",
]

EventType = Literal[
    "status",
    "node_started",
    "node_completed",
    "node_failed",
    "final",
    "error",
]


class PipelineEvent(BaseModel):
    """One row in the pipeline event log; one frame on the SSE stream."""

    request_id: UUID
    sequence: int = Field(..., ge=0, description="Monotonic per request_id.")
    event_type: EventType
    node: NodeName | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: datetime


class Plan(BaseModel):
    """Planner output: which specialists to dispatch and in what order."""

    specialists: list[NodeName] = Field(default_factory=list)
    reasoning: str = ""


class CritiqueState(BaseModel):
    """All-fields-optional working state shared across the LangGraph DAG.

    Each node populates only its owned subset; LangGraph merges partial returns.
    A node that fails appends to `errors` and returns; the synthesizer reports
    the gap rather than failing the run.
    """

    # Inputs
    request_id: UUID
    raw_thesis: str
    created_at: datetime

    # Per-node outputs (populated as the run proceeds)
    parsed_thesis: ParsedThesis | None = None
    plan: Plan | None = None
    structure: StructureFinding | None = None
    stress_test: list[StressTestClaim] = Field(default_factory=list)
    bias_findings: list[BiasFinding] = Field(default_factory=list)
    disconfirming: list[DisconfirmingItem] = Field(default_factory=list)
    setup_critique: SetupCritique | None = None
    base_rates: list[BaseRateFinding] = Field(default_factory=list)
    draft_critique: CritiqueSections | None = None
    critic_findings: list[str] = Field(default_factory=list)
    final_critique: CritiqueSections | None = None

    # Cross-cutting
    cost_usd: float = 0.0
    errors: list[str] = Field(default_factory=list, description="Per-node failures; non-fatal.")
    gap_flags: list[str] = Field(default_factory=list)
