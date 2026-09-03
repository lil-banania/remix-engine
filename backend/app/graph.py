"""LangGraph workflow — the Remix Engine pipeline."""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.models.state import GraphState
from app.agents.analyzer import analyze_campaign
from app.agents.planner import plan_remixes
from app.agents.writer import write_remixes
from app.agents.checker import check_quality
from app.agents.visual_director import generate_visuals


def _should_generate_visuals(state: GraphState) -> str:
    """Route: run visual director if visual formats were requested."""
    if state.visual_formats:
        return "visual_direct"
    return END


def build_graph() -> StateGraph:
    """Build and compile the Remix Engine graph.

    Flow:
        analyze → plan → write → check → [visual_direct] → END

    The visual_direct node runs only if visual_formats is non-empty.
    """
    graph = StateGraph(GraphState)

    # Add nodes
    graph.add_node("analyze", analyze_campaign)
    graph.add_node("plan", plan_remixes)
    graph.add_node("write", write_remixes)
    graph.add_node("check", check_quality)
    graph.add_node("visual_direct", generate_visuals)

    # Define edges
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "plan")
    graph.add_edge("plan", "write")
    graph.add_edge("write", "check")
    graph.add_conditional_edges("check", _should_generate_visuals)
    graph.add_edge("visual_direct", END)

    return graph.compile()


# Singleton compiled graph
remix_graph = build_graph()
