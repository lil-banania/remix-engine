"""Data models for the Visual Director agent."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VisualFormat(str, Enum):
    TIKTOK = "tiktok"
    STORY = "story"
    PRINT = "print"
    STORYBOARD = "storyboard"
    LINKEDIN = "linkedin"
    WEB = "web"
    NEWSLETTER = "newsletter"
    OOH = "ooh"


VISUAL_FORMAT_SPECS: dict[VisualFormat, dict] = {
    VisualFormat.TIKTOK: {
        "label": "TikTok / Reels",
        "aspect_ratio": "9:16",
        "description": "Scroll-stopping vertical thumbnail, bold and dynamic, content-creator energy",
    },
    VisualFormat.STORY: {
        "label": "Instagram Story",
        "aspect_ratio": "9:16",
        "description": "Polished brand moment, swipeable feel, aspirational lifestyle",
    },
    VisualFormat.PRINT: {
        "label": "Affiche / Print",
        "aspect_ratio": "3:4",
        "description": "Classic advertising poster, strong visual hierarchy, headline-dominant",
    },
    VisualFormat.STORYBOARD: {
        "label": "Storyboard",
        "aspect_ratio": "16:9",
        "description": "4-frame narrative sequence: setup, tension, reveal, payoff",
    },
    VisualFormat.LINKEDIN: {
        "label": "LinkedIn Post",
        "aspect_ratio": "1.91:1",
        "description": "Professional B2B post card, clean corporate visual, thought-leadership energy",
    },
    VisualFormat.WEB: {
        "label": "Page Web",
        "aspect_ratio": "16:9",
        "description": "Hero section of an interactive web experience, immersive and responsive",
    },
    VisualFormat.NEWSLETTER: {
        "label": "Newsletter",
        "aspect_ratio": "600:400",
        "description": "Email header visual, 600px-wide, clean and brand-forward",
    },
    VisualFormat.OOH: {
        "label": "OOH Digital",
        "aspect_ratio": "16:9",
        "description": "Digital billboard or urban screen, bold at distance, high-impact visual",
    },
}


class VisualBrief(BaseModel):
    """Creative brief for one visual format."""

    format: VisualFormat
    image_prompt: str = Field(description="Detailed prompt for AI image generation")
    headline: str = Field(description="Main copy overlay")
    subline: str = Field(default="", description="Secondary copy / CTA")
    art_direction: str = Field(description="Color, mood, style notes")


class StoryboardFrame(BaseModel):
    """One frame in a storyboard sequence."""

    image_prompt: str
    caption: str
    image_b64: Optional[str] = Field(
        default=None,
        description="Base64-encoded generated image",
        exclude=True,  # Don't serialize in API responses by default
    )


class VisualOutput(BaseModel):
    """Generated visual for one format, with brief and optional image."""

    format: VisualFormat
    format_label: str
    headline: str
    subline: str = ""
    art_direction: str = ""
    image_prompt: str = ""
    image_b64: Optional[str] = Field(
        default=None,
        description="Base64-encoded generated image (excluded from default serialization)",
    )
    storyboard_frames: Optional[list[StoryboardFrame]] = Field(
        default=None,
        description="Storyboard frames (only for storyboard format)",
    )
    scenario_id: Optional[int] = Field(
        default=None,
        description="Scenario ID this visual belongs to (None for legacy single-scenario mode)",
    )

    def has_image(self) -> bool:
        if self.storyboard_frames:
            return any(f.image_b64 for f in self.storyboard_frames)
        return self.image_b64 is not None

    def to_api_dict(self) -> dict:
        """Serialize for API response, including image data."""
        d = {
            "format": self.format.value,
            "format_label": self.format_label,
            "headline": self.headline,
            "subline": self.subline,
            "art_direction": self.art_direction,
            "image_prompt": self.image_prompt,
            "has_image": self.has_image(),
            "scenario_id": self.scenario_id,
        }
        if self.image_b64:
            d["image_b64"] = self.image_b64
        if self.storyboard_frames:
            d["storyboard_frames"] = [
                {
                    "caption": f.caption,
                    "image_prompt": f.image_prompt,
                    "has_image": f.image_b64 is not None,
                    "image_b64": f.image_b64,
                }
                for f in self.storyboard_frames
            ]
        return d
