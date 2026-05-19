"""Public HTTP API request and response models.

These Pydantic schemas are the source of truth for what the API accepts and
returns. The FastAPI router in `app.api.v1.critique` references these models;
the frontend consumes their JSON shape via `openapi-typescript` against the
committed `backend/app/api/openapi.json`.

Internal-only fields (raw LLM outputs, intermediate state) live on
`app.models.state.CritiqueState`, not here.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Markets the system supports. Bare US tickers, NSE/BSE suffixes for India,
# `.DE` for XETRA. Anything else is rejected by the parser.
Market = Literal["US", "IN", "DE"]
Direction = Literal["long", "short"]
SetupKind = Literal["orb", "sr_bounce", "other"]
Verdict = Literal["strong", "marginal", "weak"]
RequestStatus = Literal["queued", "pending", "complete", "partial", "failed"]
BiasKind = Literal[
    "anchoring",
    "recency",
    "confirmation",
    "overconfidence",
    "revenge",
]
Severity = Literal["low", "medium", "high"]
ClaimVerdict = Literal["supported", "contradicted", "unverifiable"]


# --- Request ---------------------------------------------------------------


class CritiqueRequest(BaseModel):
    """Submission body for `POST /api/v1/critique`.

    `thesis` is free-text English; the parser is responsible for extracting
    structured fields. The ticker inside the thesis must carry an exchange
    indicator (`AAPL` / `INFY.NS` / `SAP.DE`); parser will fail closed otherwise.
    """

    thesis: str = Field(..., min_length=10, max_length=4000)


# --- Acknowledgement (returned by POST) ------------------------------------


class CritiqueQueued(BaseModel):
    """202 response from `POST /api/v1/critique`."""

    request_id: UUID
    status: Literal["queued"] = "queued"


# --- Parsed thesis (also surfaced in the response for transparency) ---------


class ParsedThesis(BaseModel):
    """Structured form of the user's free-text thesis."""

    ticker: str
    exchange: Market
    direction: Direction
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    setup: SetupKind
    time_horizon: str | None = None
    claims: list[str] = Field(
        default_factory=list,
        description="Verifiable claims for the stress-tester.",
    )
    raw_confidence_words: list[str] = Field(
        default_factory=list,
        description="Phrases the bias detector pre-scan flagged.",
    )


# --- Section findings ------------------------------------------------------


class StructureFinding(BaseModel):
    """Output of the structure critic (trade mechanics)."""

    rr_ratio: float | None = None
    atr_14: float | None = None
    stop_to_atr_multiple: float | None = None
    sizing_note: str | None = None
    verdict: str = Field(..., description="Prose summary of the mechanics critique.")
    issues: list[str] = Field(default_factory=list)


class StressTestClaim(BaseModel):
    """One claim from the thesis, with the stress-tester's verdict."""

    claim: str
    verdict: ClaimVerdict
    evidence: list[str] = Field(default_factory=list)


class BiasFinding(BaseModel):
    """One bias the bias detector identified in the thesis."""

    bias: BiasKind
    span: str = Field(..., description="The phrase from the thesis that triggered the flag.")
    severity: Severity
    explanation: str


class DisconfirmingItem(BaseModel):
    """A piece of evidence that runs counter to the thesis."""

    source: str = Field(..., description="e.g. 'NewsAPI', 'YahooFinance RSS', 'EDGAR'.")
    headline: str
    url: str | None = None
    relevance: Literal["ticker", "sector", "catalyst", "peer"]
    summary: str


class BaseRateFinding(BaseModel):
    """Historical hit rate for the closest matching setup bucket."""

    setup: SetupKind
    bucket: dict[str, str | float | int] = Field(default_factory=dict)
    sample_size: int = Field(..., ge=0)
    hit_rate: float = Field(..., ge=0.0, le=1.0)


class CritiqueSections(BaseModel):
    """The four-section critique body."""

    mechanics: StructureFinding
    stress_test: list[StressTestClaim] = Field(default_factory=list)
    bias: list[BiasFinding] = Field(default_factory=list)
    disconfirming: list[DisconfirmingItem] = Field(default_factory=list)
    base_rates: list[BaseRateFinding] = Field(default_factory=list)


# --- Full response (returned by GET when status != pending) ----------------


class CritiqueResponse(BaseModel):
    """Final critique body. Mirrors what the synthesizer produced and the critic verified."""

    request_id: UUID
    status: Literal["complete", "partial", "failed"]
    verdict: Verdict | None = Field(
        None,
        description="Top-line characterization. Absent on `failed`.",
    )
    raw_thesis: str
    parsed_thesis: ParsedThesis | None = None
    sections: CritiqueSections | None = None
    gap_flags: list[str] = Field(
        default_factory=list,
        description="Reasons a partial critique is partial; e.g. 'newsapi_unavailable'.",
    )
    cost_usd: float = Field(0.0, ge=0.0)
    created_at: datetime
    completed_at: datetime | None = None


class CritiquePending(BaseModel):
    """200 response from `GET /api/v1/critique/{id}` when work is still in flight."""

    request_id: UUID
    status: Literal["pending"] = "pending"
    created_at: datetime


# --- Health ----------------------------------------------------------------


class HealthResponse(BaseModel):
    """`GET /api/v1/health` body."""

    status: Literal["ok", "degraded", "down"]
    version: str
    checks: dict[str, str] = Field(
        default_factory=dict,
        description="Per-dependency state: db, redis, last_llm.",
    )
