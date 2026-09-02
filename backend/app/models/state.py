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


class GraphState(BaseModel):
    """Shared state across all agents in the remix graph."""

    # --- Input ---
    campaign_brief: str = Field(description="Raw campaign brief from the user")

    # --- Campaign Analyzer output ---
    analysis: Optional[CampaignAnalysis] = None

    # --- Remix Planner output ---
    remix_request: Optional[RemixRequest] = None
    planned_formats: list[RemixFormat] = Field(default_factory=list)

    # --- Creative Writer output ---
    remixes: list[RemixOutput] = Field(default_factory=list)

    # --- Quality Checker output ---
    results: list[RemixResult] = Field(default_factory=list)

    # --- Control flow ---
    current_step: str = Field(default="input")
    error: Optional[str] = None
