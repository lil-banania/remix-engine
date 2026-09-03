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
) -> RemixOutput:
    """Generate a single remix for one format."""
    specs = FORMAT_SPECS[fmt]
    llm = get_llm().with_structured_output(RemixOutput)

    audience_line = f"\nTarget audience shift: {audience}" if audience else ""
    market_line = f"\nTarget market shift: {market}" if market else ""

    prompt = f"""\
CAMPAIGN ANALYSIS:
{analysis_text}

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
    """Generate all remixes in parallel (fan-out)."""
    if not state.analysis or not state.planned_formats:
        return {"error": "Missing analysis or planned formats"}

    analysis_text = state.analysis.model_dump_json(indent=2)

    audience = state.remix_request.target_audience if state.remix_request else None
    market = state.remix_request.target_market if state.remix_request else None

    # Fan-out: generate all remixes in parallel
    tasks = [
        _generate_one_remix(analysis_text, fmt, audience, market)
        for fmt in state.planned_formats
    ]
    remixes = await asyncio.gather(*tasks)

    return {
        "remixes": list(remixes),
        "current_step": "written",
    }
