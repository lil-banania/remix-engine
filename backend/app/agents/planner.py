"""Remix Planner agent — plans the declinations based on user choices."""

from __future__ import annotations

from app.models.campaign import FORMAT_SPECS
from app.models.state import GraphState


async def plan_remixes(state: GraphState) -> dict:
    """Plan the remix executions based on the remix request.

    This agent is intentionally simple in the MVP: it validates the
    requested formats and enriches them with specs from the catalog.
    In future versions it will use an LLM to suggest optimal format
    combinations and identify creative tensions per format.
    """
    if not state.remix_request:
        return {"error": "No remix request provided"}

    planned = []
    for fmt in state.remix_request.formats:
        if fmt in FORMAT_SPECS:
            planned.append(fmt)

    if not planned:
        return {"error": "No valid formats selected"}

    return {
        "planned_formats": planned,
        "current_step": "planned",
    }
