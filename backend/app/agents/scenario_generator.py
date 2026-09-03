"""Scenario Generator agent — produces 3 creative directions from the analysis."""

from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.scenario import CreativeScenario, ScenarioSet
from app.models.state import GraphState

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """\
You are a senior creative director at a top advertising agency (TBWA, Wieden+Kennedy).
Your job is to propose 3 DISTINCT creative directions from a single campaign brief analysis.

Each scenario should:
1. Stay true to the brand DNA and consumer insight
2. Offer a genuinely DIFFERENT creative angle — not just a variation in tone
3. Be producible across multiple formats (video, social, print, digital)

The 3 scenarios should cover a spectrum:
- **Scenario 1**: The safe bet — the most logical, brand-coherent extension of the concept
- **Scenario 2**: The bold move — pushes the concept further, takes a creative risk
- **Scenario 3**: The wildcard — unexpected angle, could be brilliant or polarizing

For each, provide:
- **title**: 3-5 word name for this direction
- **angle**: How this scenario reinterprets the central concept (2-3 sentences)
- **mood**: Visual and tonal direction (1 sentence — colors, energy, references)

Respond in the same language as the analysis.
"""


def get_llm() -> ChatAnthropic:
    return ChatAnthropic(model=MODEL, max_tokens=2048)


async def generate_scenarios(state: GraphState) -> dict:
    """Generate 3 creative scenarios from the campaign analysis."""
    print("[scenario_generator] === Generating 3 creative scenarios ===")

    if not state.analysis:
        return {"error": "Missing campaign analysis"}

    llm = get_llm().with_structured_output(ScenarioSet)
    analysis_text = state.analysis.model_dump_json(indent=2)

    prompt = f"""\
CAMPAIGN ANALYSIS:
{analysis_text}

Generate 3 distinct creative scenarios for this campaign.
Each must offer a genuinely different creative direction while staying true to the brand."""

    try:
        result = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        scenarios = result.scenarios
        print(f"[scenario_generator] Generated {len(scenarios)} scenarios:")
        for s in scenarios:
            print(f"  [{s.id}] {s.title}: {s.angle[:60]}...")

        return {
            "scenarios": scenarios,
            "current_step": "scenarios_ready",
        }
    except Exception as e:
        print(f"[scenario_generator] ERROR: {e}")
        return {"error": f"Scenario generation failed: {e}"}
