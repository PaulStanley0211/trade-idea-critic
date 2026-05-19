"""Compiled LangGraph for the critique pipeline.

Phase 1.3 stub: every node is a pure async function returning canned data, so
the graph wiring and SSE streaming work end-to-end without requiring LLM calls,
network access, or a populated database. Subsequent phases swap node bodies
with real implementations - the graph shape, state schema, and edges stay.

Node order (sequential in W1 for simplicity; W2 fans out specialists in
parallel):

    parser -> planner -> structure_critic -> stress_tester -> bias_detector
        -> disconfirming_retriever -> setup_specialist -> base_rate_evaluator
        -> synthesizer -> critic -> output_filter -> END

Each node returns a partial-state dict that LangGraph merges into the running
`CritiqueState`. Errors append to `state.errors` and the synthesizer reports
the gap; nodes do not raise.
"""

from __future__ import annotations

import asyncio
from typing import Any

from langgraph.graph import END, START, StateGraph

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
from app.models.state import CritiqueState, Plan

# Approximate per-node delay for the W1 stub so the SSE stream is observably
# streamed in the UI. Removed when nodes do real work.
_STUB_DELAY_SEC = 0.15


async def parser(state: CritiqueState) -> dict[str, Any]:
    """Stub: produce a canned `ParsedThesis`. W2 replaces with an LLM call."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    parsed = ParsedThesis(
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
    )
    return {"parsed_thesis": parsed}


async def planner(state: CritiqueState) -> dict[str, Any]:
    """Stub: pick all specialists. W2 makes this LLM-driven and conditional."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    plan = Plan(
        specialists=[
            "structure_critic",
            "stress_tester",
            "bias_detector",
            "disconfirming_retriever",
            "setup_specialist",
            "base_rate_evaluator",
        ],
        reasoning="Stub: dispatch every specialist regardless of input.",
    )
    return {"plan": plan}


async def structure_critic(state: CritiqueState) -> dict[str, Any]:
    """Stub: canned `StructureFinding`. W2 computes R/R and ATR for real."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    return {
        "structure": StructureFinding(
            rr_ratio=2.0,
            atr_14=2.5,
            stop_to_atr_multiple=1.2,
            sizing_note="Stub: sizing not evaluated in W1.",
            verdict="Stub mechanics: R/R is acceptable; stop within ATR.",
            issues=[],
        ),
    }


async def stress_tester(state: CritiqueState) -> dict[str, Any]:
    """Stub: emit one unverifiable claim. W3 verifies each claim."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    return {
        "stress_test": [
            StressTestClaim(
                claim="volume above 20-day average",
                verdict="unverifiable",
                evidence=["Stub: yfinance not wired in W1."],
            ),
        ],
    }


async def bias_detector(state: CritiqueState) -> dict[str, Any]:
    """Stub: one low-severity recency bias. W3 wires regex + LLM detection."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    return {
        "bias_findings": [
            BiasFinding(
                bias="recency",
                span="(stub) tech sector strong today",
                severity="low",
                explanation="Stub: bias detector not wired in W1.",
            ),
        ],
    }


async def disconfirming_retriever(state: CritiqueState) -> dict[str, Any]:
    """Stub: one canned disconfirming item. W3 wires NewsAPI + RSS."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    return {
        "disconfirming": [
            DisconfirmingItem(
                source="(stub)",
                headline="Stub headline: news retriever not wired in W1.",
                url=None,
                relevance="ticker",
                summary="Replaced in W3 with NewsAPI + RSS results.",
            ),
        ],
    }


async def setup_specialist(state: CritiqueState) -> dict[str, Any]:
    """Stub: marginal-quality canned ORB critique. W2 loads docs/setups/orb.md."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    return {
        "setup_critique": SetupCritique(
            setup="orb",
            quality="marginal",
            checks=[
                {"rule": "range_window_observed", "status": "stub", "evidence": "n/a"},
                {"rule": "volume_confirmation", "status": "stub", "evidence": "n/a"},
            ],
            narrative="Stub: setup specialist not wired in W1.",
        ),
    }


async def base_rate_evaluator(state: CritiqueState) -> dict[str, Any]:
    """Stub: empty base rates. W2 reads from the precomputed `base_rates` table."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    empty: list[BaseRateFinding] = []
    return {"base_rates": empty}


async def synthesizer(state: CritiqueState) -> dict[str, Any]:
    """Compose `draft_critique` from specialist outputs. W2 makes this LLM-driven."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    if state.structure is None:
        # Critic + output_filter still run so the user gets an explicit gap critique.
        gap = "structure_unavailable"
        return {"gap_flags": [*state.gap_flags, gap]}
    draft = CritiqueSections(
        mechanics=state.structure,
        stress_test=state.stress_test,
        bias=state.bias_findings,
        disconfirming=state.disconfirming,
        base_rates=state.base_rates,
        setup_critique=state.setup_critique,
    )
    return {"draft_critique": draft}


async def critic(state: CritiqueState) -> dict[str, Any]:
    """Stub: pass-through. W3 verifies each quantitative sentence and loops up to 3x."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    if state.draft_critique is None:
        return {"critic_findings": ["draft_critique missing"]}
    return {"critic_findings": []}


_BANNED = ("buy", "sell", "recommend")


async def output_filter(state: CritiqueState) -> dict[str, Any]:
    """Drop the verdict if any banned word leaks through. W2's critic does the rewording."""
    await asyncio.sleep(_STUB_DELAY_SEC)
    if state.draft_critique is None:
        return {"final_critique": None}
    # Render the draft to text once and scan; the critic rewrites flagged spans in W2.
    serialized = state.draft_critique.model_dump_json().lower()
    flagged = [w for w in _BANNED if f" {w} " in f" {serialized} "]
    if flagged:
        return {
            "final_critique": state.draft_critique,
            "gap_flags": [*state.gap_flags, *[f"output_filter_flagged:{w}" for w in flagged]],
        }
    return {"final_critique": state.draft_critique}


def _build_graph() -> Any:
    """Wire the stub graph. Sequential in W1; W2 fans out specialists in parallel."""
    builder = StateGraph(CritiqueState)
    builder.add_node("parser", parser)
    builder.add_node("planner", planner)
    builder.add_node("structure_critic", structure_critic)
    builder.add_node("stress_tester", stress_tester)
    builder.add_node("bias_detector", bias_detector)
    builder.add_node("disconfirming_retriever", disconfirming_retriever)
    builder.add_node("setup_specialist", setup_specialist)
    builder.add_node("base_rate_evaluator", base_rate_evaluator)
    builder.add_node("synthesizer", synthesizer)
    builder.add_node("critic", critic)
    builder.add_node("output_filter", output_filter)

    builder.add_edge(START, "parser")
    builder.add_edge("parser", "planner")
    builder.add_edge("planner", "structure_critic")
    builder.add_edge("structure_critic", "stress_tester")
    builder.add_edge("stress_tester", "bias_detector")
    builder.add_edge("bias_detector", "disconfirming_retriever")
    builder.add_edge("disconfirming_retriever", "setup_specialist")
    builder.add_edge("setup_specialist", "base_rate_evaluator")
    builder.add_edge("base_rate_evaluator", "synthesizer")
    builder.add_edge("synthesizer", "critic")
    builder.add_edge("critic", "output_filter")
    builder.add_edge("output_filter", END)
    return builder.compile()


graph = _build_graph()
