"""Data models for multi-scenario creative directions."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.campaign import RemixResult
from app.models.visuals import VisualOutput


class CreativeScenario(BaseModel):
    """One creative direction derived from the campaign analysis."""

    id: int = Field(description="Scenario number (1, 2, or 3)")
    title: str = Field(description="Short name for this direction (3-5 words)")
    angle: str = Field(
        description="The creative twist — how this scenario reinterprets the concept"
    )
    mood: str = Field(
        description="Visual and tonal mood for this direction (1 sentence)"
    )


class ScenarioSet(BaseModel):
    """The set of 3 creative scenarios generated from analysis."""

    scenarios: list[CreativeScenario] = Field(
        min_length=1,
        max_length=5,
        description="Creative scenarios (typically 3)",
    )


class ScenarioResult(BaseModel):
    """Complete output for one scenario — remixes + visuals."""

    scenario: CreativeScenario
    results: list[RemixResult] = Field(default_factory=list)
    visuals: list[dict] = Field(default_factory=list)
