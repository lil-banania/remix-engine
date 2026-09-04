"""Creative Writer agent — generates each remix declination."""

from __future__ import annotations

import asyncio
import os

from langchain_anthropic import ChatAnthropic

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.campaign import FORMAT_SPECS, RemixFormat, RemixOutput
from app.models.state import GraphState

SYSTEM_PROMPT = """\
You are a creative director at a world-class advertising agency. You specialize in adapting campaign ideas across formats and platforms while preserving the creative DNA.

You will receive:
1. A campaign analysis (brand, insight, concept, tone, existing executions)
2. A target format with its technical specifications
3. Optional audience or market shift

Your job is to create a complete creative declination for the target format:

- **Adapted Concept**: How does the central IDEA (not just the visuals) translate into this new format? This is the most important part. Don't just shrink the TV spot — reimagine the mechanism for this medium.
- **Headline / Hook**: The main copy, adapted to the format's conventions
- **Narrative Description**: What happens visually (or aurally). Be specific enough that a creative team could produce it.
- **Production Notes**: What changes vs the original, what new assets are needed
- **Tone Check**: Confirm the tone stays coherent with the brand

Think like a creative who has to present this to a client tomorrow. It needs to feel inevitable — like this format was always part of the plan.

Respond in the same language as the campaign analysis.
"""


def get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=MODEL,
        max_tokens=4096,
    )


async def _generate_one_remix(
    analysis_text: str,
    fmt: RemixFormat,
    audience: str | None,
    market: str | None,
    scenario_context: str = "",
) -> RemixOutput:
    """Generate a single remix for one format."""
    specs = FORMAT_SPECS[fmt]
    llm = get_llm().with_structured_output(RemixOutput)

    audience_line = f"\nTarget audience shift: {audience}" if audience else ""
    market_line = f"\nTarget market shift: {market}" if market else ""

    prompt = f"""\
CAMPAIGN ANALYSIS:
{analysis_text}
{scenario_context}
TARGET FORMAT: {specs['label']}
- Duration: {specs['duration']}
- Aspect ratio: {specs['aspect_ratio']}
- Constraints: {specs['constraints']}
{audience_line}{market_line}

Generate the creative declination for this format."""

    result = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    # Ensure format metadata is correct
    result.format = fmt
    result.format_label = specs["label"]
    result.format_specs = f"{specs['duration']} | {specs['aspect_ratio']} | {specs['constraints']}"

    return result


async def write_remixes(state: GraphState) -> dict:
    """Generate all remixes in parallel, per scenario if scenarios exist."""
    if not state.analysis or not state.planned_formats:
        return {"error": "Missing analysis or planned formats"}

    analysis_text = state.analysis.model_dump_json(indent=2)
    audience = state.remix_request.target_audience if state.remix_request else None
    market = state.remix_request.target_market if state.remix_request else None

    scenarios = state.scenarios or []

    if not scenarios:
        # Legacy mode: no scenarios, generate remixes directly
        tasks = [
            _generate_one_remix(analysis_text, fmt, audience, market)
            for fmt in state.planned_formats
        ]
        remixes = await asyncio.gather(*tasks)
        return {
            "remixes": list(remixes),
            "current_step": "written",
        }

    # Multi-scenario mode: generate remixes for each scenario × format
    from app.models.scenario import ScenarioResult

    print(f"[writer] Generating remixes for {len(scenarios)} scenarios × {len(state.planned_formats)} formats")

    all_tasks = []
    task_map = []  # (scenario_index, format) for each task

    for i, scenario in enumerate(scenarios):
        scenario_context = f"""
CREATIVE DIRECTION FOR THIS REMIX:
- Direction: "{scenario.title}"
- Angle: {scenario.angle}
- Mood: {scenario.mood}

IMPORTANT: Your remix MUST follow this specific creative direction. The concept adaptation should reflect this angle, not just the generic campaign concept.
"""
        for fmt in state.planned_formats:
            all_tasks.append(
                _generate_one_remix(analysis_text, fmt, audience, market, scenario_context)
            )
            task_map.append((i, fmt))

    all_remixes_raw = await asyncio.gather(*all_tasks)

    # Tag each remix with its scenario_id and group by scenario
    scenario_remixes: dict[int, list] = {i: [] for i in range(len(scenarios))}
    for remix, (scenario_idx, _fmt) in zip(all_remixes_raw, task_map):
        remix.scenario_id = scenarios[scenario_idx].id
        scenario_remixes[scenario_idx].append(remix)

    all_scenario_results = []
    all_remixes = []
    for i, scenario in enumerate(scenarios):
        remixes = scenario_remixes[i]
        all_scenario_results.append(ScenarioResult(
            scenario=scenario,
            results=[],  # filled by checker
            visuals=[],
        ))
        all_remixes.extend(remixes)
        print(f"[writer] Scenario '{scenario.title}': {len(remixes)} remixes done")

    return {
        "remixes": all_remixes,
        "scenario_results": all_scenario_results,
        "current_step": "written",
    }
