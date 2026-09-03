"""Data models for campaign analysis and remix generation."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Remix format catalog ---

class RemixFormat(str, Enum):
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"
    OOH_DIGITAL = "ooh_digital"
    RADIO_SPOT = "radio_spot"
    PODCAST_PREROLL = "podcast_preroll"
    WEB_INTERACTIVE = "web_interactive"
    PRINT_PRESS = "print_press"
    NEWSLETTER = "newsletter"
    ACTIVATION_RETAIL = "activation_retail"
    LINKEDIN_B2B = "linkedin_b2b"


FORMAT_SPECS: dict[RemixFormat, dict] = {
    RemixFormat.INSTAGRAM_REELS: {
        "label": "Instagram Reels",
        "duration": "15-60s",
        "aspect_ratio": "9:16",
        "constraints": "Hook in first 3s, text overlays, trending audio optional",
    },
    RemixFormat.TIKTOK: {
        "label": "TikTok",
        "duration": "15-60s",
        "aspect_ratio": "9:16",
        "constraints": "Native feel, no overproduced look, comment-bait CTA",
    },
    RemixFormat.OOH_DIGITAL: {
        "label": "OOH Digital (DOOH)",
        "duration": "10-15s loop",
        "aspect_ratio": "16:9 or 9:16",
        "constraints": "Readable at distance, minimal text, high contrast, no audio",
    },
    RemixFormat.RADIO_SPOT: {
        "label": "Radio Spot",
        "duration": "20-30s",
        "aspect_ratio": "N/A (audio)",
        "constraints": "Audio only, brand mention in first 5s, clear CTA",
    },
    RemixFormat.PODCAST_PREROLL: {
        "label": "Podcast Pre-roll",
        "duration": "15-30s",
        "aspect_ratio": "N/A (audio)",
        "constraints": "Conversational tone, host-read style, native integration feel",
    },
    RemixFormat.WEB_INTERACTIVE: {
        "label": "Web Interactive Experience",
        "duration": "N/A",
        "aspect_ratio": "Responsive",
        "constraints": "Scroll-driven, micro-interactions, shareable moment",
    },
    RemixFormat.PRINT_PRESS: {
        "label": "Print Press Ad",
        "duration": "N/A",
        "aspect_ratio": "Full page or double",
        "constraints": "Single visual, headline + baseline, QR code optional",
    },
    RemixFormat.NEWSLETTER: {
        "label": "Newsletter / Email",
        "duration": "N/A",
        "aspect_ratio": "600px wide",
        "constraints": "Subject line critical, single CTA, mobile-first",
    },
    RemixFormat.ACTIVATION_RETAIL: {
        "label": "Activation en magasin",
        "duration": "Variable",
        "aspect_ratio": "Physical",
        "constraints": "Experiential, photo-worthy, brand immersion, shareable",
    },
    RemixFormat.LINKEDIN_B2B: {
        "label": "LinkedIn B2B Post",
        "duration": "N/A",
        "aspect_ratio": "1:1 or 4:5",
        "constraints": "Professional tone, thought leadership angle, carousel option",
    },
}


# --- Campaign analysis models ---

class CampaignAnalysis(BaseModel):
    """The creative building blocks extracted from a campaign."""

    brand: str = Field(description="Brand name")
    category: str = Field(description="Market category / industry")
    market: str = Field(description="Geographic market (e.g. France, Global)")
    consumer_insight: str = Field(
        description="The human tension the campaign exploits"
    )
    creative_concept: str = Field(
        description="The central idea / creative mechanism"
    )
    tone_of_voice: str = Field(
        description="Tone, style, and artistic direction"
    )
    signature: str = Field(
        description="Campaign signature / tagline if any"
    )
    existing_executions: list[str] = Field(
        default_factory=list,
        description="Formats already produced for this campaign",
    )
    summary: str = Field(
        description="One-paragraph synthesis of the campaign"
    )


# --- Remix models ---

class RemixRequest(BaseModel):
    """What the user wants to remix."""

    formats: list[RemixFormat] = Field(
        min_length=1,
        max_length=5,
        description="Target formats for remix (1-5)",
    )
    target_audience: Optional[str] = Field(
        default=None,
        description="Optional audience shift (e.g. 'Gen Z', 'B2B decision makers')",
    )
    target_market: Optional[str] = Field(
        default=None,
        description="Optional market shift (e.g. 'US', 'UK')",
    )


class RemixOutput(BaseModel):
    """A single creative declination."""

    format: RemixFormat
    format_label: str
    format_specs: str = Field(description="Duration, dimensions, technical constraints")
    adapted_concept: str = Field(
        description="How the central idea translates into this format"
    )
    headline: str = Field(description="Main copy / hook")
    narrative_description: str = Field(
        description="Visual description, sequence of events, what happens"
    )
    production_notes: str = Field(
        description="What changes vs the original, what needs to be produced"
    )
    tone_check: str = Field(
        description="Verification that tone stays consistent with the brand"
    )
    scenario_id: Optional[int] = Field(
        default=None,
        description="Scenario ID this remix belongs to (None for legacy single-scenario mode)",
    )


class QualityVerdict(BaseModel):
    """Quality check result for one remix."""

    format: RemixFormat
    is_consistent: bool = Field(
        description="Whether the remix stays true to the original concept"
    )
    score: int = Field(ge=1, le=10, description="Quality score 1-10")
    strengths: list[str] = Field(description="What works well")
    issues: list[str] = Field(
        default_factory=list,
        description="Potential issues or inconsistencies",
    )
    suggestion: str = Field(
        default="",
        description="Improvement suggestion if score < 7",
    )


class RemixResult(BaseModel):
    """Final result combining the remix and its quality check."""

    remix: RemixOutput
    quality: QualityVerdict
