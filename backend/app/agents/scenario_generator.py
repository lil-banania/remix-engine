"""Scenario Generator agent — produces 3 creative directions from the analysis."""

from __future__ import annotations

import json
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
        try:
            result = await llm.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
        except Exception as parse_err:
            # Structured output may fail if the LLM returns raw JSON string
            # instead of a parsed object — fall through to manual parsing
            print(f"[scenario_generator] Structured output failed: {parse_err}")
            print("[scenario_generator] Falling back to raw JSON parsing...")
            raw_llm = get_llm()
            raw_result = await raw_llm.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt + "\n\nRespond with valid JSON matching this schema: {\"scenarios\": [{\"id\": 1, \"title\": \"...\", \"angle\": \"...\", \"mood\": \"...\"}]}"),
            ])
            raw_text = raw_result.content if hasattr(raw_result, 'content') else str(raw_result)
            if isinstance(raw_text, list):
                raw_text = raw_text[0].text if hasattr(raw_text[0], "text") else str(raw_text[0])
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            parsed = json.loads(raw_text[json_start:json_end])
            result = ScenarioSet(**parsed)

        # Handle case where structured output returns a string instead of parsed object
        if isinstance(result, str):
            print("[scenario_generator] Got string response, parsing manually...")
            parsed = json.loads(result)
            result = ScenarioSet(**parsed)
        elif isinstance(result, dict):
            print("[scenario_generator] Got dict response, parsing manually...")
            result = ScenarioSet(**result)

        scenarios = result.scenarios

        # Ensure scenario IDs are set correctly (1, 2, 3)
        for i, s in enumerate(scenarios):
            if not s.id:
                s.id = i + 1

        print(f"[scenario_generator] Generated {len(scenarios)} scenarios:")
        for s in scenarios:
            print(f"  [{s.id}] {s.title}: {s.angle[:60]}...")

        return {
            "scenarios": scenarios,
            "current_step": "scenarios_ready",
        }
    except Exception as e:
        print(f"[scenario_generator] ERROR: {e}")
        # Last resort: try without structured output
        try:
            print("[scenario_generator] Retrying without structured output...")
            raw_llm = get_llm()
            raw_result = await raw_llm.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt + "\n\nRespond with valid JSON matching this schema: {\"scenarios\": [{\"id\": 1, \"title\": \"...\", \"angle\": \"...\", \"mood\": \"...\"}]}"),
            ])
            raw_text = raw_result.content if hasattr(raw_result, 'content') else str(raw_result)
            # Extract JSON from response
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(raw_text[json_start:json_end])
                scenario_set = ScenarioSet(**parsed)
                print(f"[scenario_generator] Fallback succeeded: {len(scenario_set.scenarios)} scenarios")
                return {
                    "scenarios": scenario_set.scenarios,
                    "current_step": "scenarios_ready",
                }
        except Exception as e2:
            print(f"[scenario_generator] Fallback also failed: {e2}")

        return {"error": f"Scenario generation failed: {e}"}
