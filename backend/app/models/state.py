"""LangGraph state definition for the Remix Engine."""

from __future__ import annotations

from typing import Annotated, Optional

from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from app.models.campaign import (
    CampaignAnalysis,
    RemixFormat,
    RemixOutput,
    RemixResult,
    RemixRequest,
)
from app.models.visuals import VisualFormat, VisualOutput
from app.models.scenario import CreativeScenario, ScenarioResult


class GraphState(BaseModel):
    """Shared state across all agents in the remix graph."""

    # --- Input ---
    campaign_brief: str = Field(description="Raw campaign brief from the user")

    # --- Campaign Analyzer output ---
    analysis: Optional[CampaignAnalysis] = None

    # --- Scenario Generator output ---
    scenarios: list[CreativeScenario] = Field(default_factory=list)

    # --- Remix Planner output ---
    remix_request: Optional[RemixRequest] = None
    planned_formats: list[RemixFormat] = Field(default_factory=list)

    # --- Creative Writer output (per-scenario) ---
    remixes: list[RemixOutput] = Field(default_factory=list)
    scenario_results: list[ScenarioResult] = Field(default_factory=list)

    # --- Quality Checker output ---
    results: list[RemixResult] = Field(default_factory=list)

    # --- Visual Director ---
    visual_formats: list[VisualFormat] = Field(default_factory=list)
    visuals: list[VisualOutput] = Field(default_factory=list)

    # --- Control flow ---
    current_step: str = Field(default="input")
    error: Optional[str] = None
