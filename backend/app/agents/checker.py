"""Quality Checker agent — verifies consistency of each remix with the original."""

from __future__ import annotations

import asyncio
import os

from langchain_anthropic import ChatAnthropic

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.campaign import QualityVerdict, RemixOutput, RemixResult
from app.models.state import GraphState

SYSTEM_PROMPT = """\
You are a creative quality reviewer at a top advertising agency. Your role is to evaluate whether a campaign declination (remix) stays true to the original campaign's creative DNA.

You will receive:
1. The original campaign analysis (insight, concept, tone, brand)
2. A creative declination for a specific format

Evaluate on these criteria:
- **Concept fidelity**: Does the remix preserve the CENTRAL IDEA, not just the surface aesthetics?
- **Insight connection**: Is the original consumer insight still driving the execution?
- **Tone consistency**: Does it feel like the same brand speaking?
- **Format fit**: Does the execution genuinely leverage the format's strengths, or is it just a resize?
- **Producibility**: Could a creative team actually produce this with the notes given?

Score from 1-10:
- 9-10: Brilliant adaptation, adds to the campaign
- 7-8: Solid, producible, on-brand
- 5-6: Decent but feels like a resize rather than a true adaptation
- 3-4: Loses the concept or misses the format's potential
- 1-2: Off-brand or incoherent

Be constructive but honest. A DC reading this should trust your judgment.

Respond in the same language as the remix.
"""


def get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=MODEL,
        max_tokens=1500,
    )


async def _check_one_remix(
    analysis_text: str,
    remix: RemixOutput,
) -> RemixResult:
    """Quality-check a single remix."""
    llm = get_llm().with_structured_output(QualityVerdict)

    prompt = f"""\
ORIGINAL CAMPAIGN ANALYSIS:
{analysis_text}

REMIX TO EVALUATE:
Format: {remix.format_label}
Adapted Concept: {remix.adapted_concept}
Headline: {remix.headline}
Narrative: {remix.narrative_description}
Production Notes: {remix.production_notes}
Tone Check (self-reported): {remix.tone_check}

Evaluate this declination."""

    verdict = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])
    verdict.format = remix.format

    return RemixResult(remix=remix, quality=verdict)


async def check_quality(state: GraphState) -> dict:
    """Quality-check all remixes in parallel, grouped by scenario if applicable."""
    if not state.analysis or not state.remixes:
        return {"error": "Missing analysis or remixes"}

    analysis_text = state.analysis.model_dump_json(indent=2)

    tasks = [
        _check_one_remix(analysis_text, remix)
        for remix in state.remixes
    ]
    results = await asyncio.gather(*tasks)
    results = list(results)

    # If we have scenarios, group results by scenario_id
    if state.scenarios and state.scenario_results:
        from app.models.scenario import ScenarioResult

        scenario_map: dict[int, list[RemixResult]] = {}
        for r in results:
            sid = getattr(r.remix, "scenario_id", None)
            if sid is not None:
                scenario_map.setdefault(sid, []).append(r)

        updated_scenario_results = []
        for sr in state.scenario_results:
            updated_scenario_results.append(ScenarioResult(
                scenario=sr.scenario,
                results=scenario_map.get(sr.scenario.id, []),
                visuals=[],
            ))

        return {
            "results": results,
            "scenario_results": updated_scenario_results,
            "current_step": "checked",
        }

    return {
        "results": results,
        "current_step": "checked",
    }
