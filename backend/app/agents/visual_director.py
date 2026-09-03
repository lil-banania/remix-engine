"""Visual Director agent — generates image briefs and visual mockups via Nano Banana."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import time

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.campaign import RemixOutput
from app.models.state import GraphState
from app.models.visuals import (
    VisualBrief,
    VisualFormat,
    VisualOutput,
    StoryboardFrame,
    VISUAL_FORMAT_SPECS,
)

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-image")

SYSTEM_PROMPT = """\
You are the Visual Director of the Campaign Remix Engine.
You receive a validated creative concept and brand analysis.
Your job is to generate precise image generation prompts for advertising formats.

## Your task
For each requested format, generate:
1. A detailed image generation prompt (in English, optimized for AI image generation)
2. A headline text overlay (in the same language as the concept, max 8 words, punchy)
3. A subline / CTA (same language, max 12 words)
4. Art direction notes (colors, mood, style — 1 sentence)

## Format guidelines
- **TikTok / Reels** (9:16): scroll-stopping, bold, content-creator energy
- **Instagram Story** (9:16): polished brand moment, swipeable, aspirational
- **Print / Affiche** (3:4): classic poster, strong visual hierarchy, headline-dominant
- **Storyboard** (16:9): 4 sequential prompts — setup → tension → reveal → payoff

## Rules
- Image prompts must be vivid, specific, and photorealistic by default
- NEVER include text, letters, or words in image prompts
- Each prompt: subject, action, setting, lighting, camera angle, mood
- The prompts should feel like a cohesive campaign
- Respond in valid JSON only

Respond in the same language as the concept for headlines and sublines.
"""


def get_llm() -> ChatAnthropic:
    return ChatAnthropic(model=MODEL, max_tokens=4096)


def _get_gemini_client():
    """Get Gemini client for image generation."""
    if not GEMINI_KEY:
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_KEY)
    except ImportError:
        return None


async def _generate_image(prompt: str, gemini_client) -> str | None:
    """Generate one image via Nano Banana. Returns base64 or None."""
    if not gemini_client:
        return None
    try:
        from google import genai
        result = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt + " No text, letters, or words in the image.",
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        for part in result.candidates[0].content.parts:
            if part.inline_data:
                return base64.b64encode(part.inline_data.data).decode("utf-8")
        return None
    except Exception as e:
        print(f"  [visual_director] Image generation error: {e}")
        return None


async def _generate_briefs(
    concept: str,
    brand: str,
    analysis_text: str,
    visual_formats: list[VisualFormat],
) -> dict:
    """Use Claude to generate visual briefs for requested formats."""
    llm = get_llm()

    format_list = "\n".join(
        f"- **{VISUAL_FORMAT_SPECS[f]['label']}** ({VISUAL_FORMAT_SPECS[f]['aspect_ratio']}): "
        f"{VISUAL_FORMAT_SPECS[f]['description']}"
        for f in visual_formats
    )

    # Build expected JSON structure
    json_keys = []
    for f in visual_formats:
        if f == VisualFormat.STORYBOARD:
            json_keys.append(
                f'  "{f.value}": {{\n'
                f'    "frames": [\n'
                f'      {{"image_prompt": "...", "caption": "..."}},\n'
                f'      {{"image_prompt": "...", "caption": "..."}},\n'
                f'      {{"image_prompt": "...", "caption": "..."}},\n'
                f'      {{"image_prompt": "...", "caption": "..."}}\n'
                f'    ],\n'
                f'    "headline": "...",\n'
                f'    "art_direction": "..."\n'
                f'  }}'
            )
        else:
            json_keys.append(
                f'  "{f.value}": {{\n'
                f'    "image_prompt": "...",\n'
                f'    "headline": "...",\n'
                f'    "subline": "...",\n'
                f'    "art_direction": "..."\n'
                f'  }}'
            )

    json_structure = "{\n" + ",\n".join(json_keys) + "\n}"

    prompt = f"""\
CAMPAIGN ANALYSIS:
{analysis_text}

BRAND: {brand}
CONCEPT: {concept}

FORMATS TO GENERATE:
{format_list}

Return ONLY valid JSON with this structure:
{json_structure}
"""

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    text = response.content
    if isinstance(text, list):
        text = text[0].text if hasattr(text[0], "text") else str(text[0])

    # Extract JSON
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    return json.loads(text.strip())


async def generate_visuals(state: GraphState) -> dict:
    """Generate visual briefs and images for requested formats.

    This is the main LangGraph node function.
    """
    print("[visual_director] === Starting visual generation ===")

    if not state.analysis:
        print("[visual_director] ERROR: Missing campaign analysis")
        return {"error": "Missing campaign analysis"}

    # Determine which visual formats to generate
    visual_formats = state.visual_formats or []
    if not visual_formats:
        # Default: generate all 4 if no specific request
        visual_formats = list(VisualFormat)

    print(f"[visual_director] Formats requested: {[f.value for f in visual_formats]}")

    brand = state.analysis.brand
    concept = state.analysis.creative_concept
    analysis_text = state.analysis.model_dump_json(indent=2)

    # Step 1: Generate creative briefs via Claude
    print(f"[visual_director] Generating briefs via {MODEL}...")
    try:
        briefs_data = await _generate_briefs(
            concept, brand, analysis_text, visual_formats,
        )
        print(f"[visual_director] Briefs generated OK — keys: {list(briefs_data.keys())}")
    except Exception as e:
        print(f"[visual_director] ERROR: Brief generation failed: {e}")
        return {"error": f"Brief generation failed: {e}"}

    # Step 2: Generate images via Nano Banana
    gemini_client = _get_gemini_client()
    print(f"[visual_director] Gemini client: {'OK' if gemini_client else 'NONE (no GEMINI_API_KEY)'}")
    outputs: list[VisualOutput] = []

    for fmt in visual_formats:
        fmt_key = fmt.value
        brief_data = briefs_data.get(fmt_key, {})

        if fmt == VisualFormat.STORYBOARD:
            # Storyboard: 4 frames
            frames_data = brief_data.get("frames", [])
            frame_images = []
            frames = []
            for i, fd in enumerate(frames_data[:4]):
                img = None
                if gemini_client:
                    img = await _generate_image(fd.get("image_prompt", ""), gemini_client)
                    # Rate limit pause
                    await asyncio.sleep(2)
                frames.append(StoryboardFrame(
                    image_prompt=fd.get("image_prompt", ""),
                    caption=fd.get("caption", f"Frame {i+1}"),
                    image_b64=img,
                ))

            outputs.append(VisualOutput(
                format=fmt,
                format_label=VISUAL_FORMAT_SPECS[fmt]["label"],
                headline=brief_data.get("headline", ""),
                subline="",
                art_direction=brief_data.get("art_direction", ""),
                image_prompt="",
                image_b64=None,
                storyboard_frames=frames,
            ))
        else:
            # Single-image format
            img = None
            if gemini_client:
                img = await _generate_image(
                    brief_data.get("image_prompt", ""), gemini_client
                )
                await asyncio.sleep(2)

            outputs.append(VisualOutput(
                format=fmt,
                format_label=VISUAL_FORMAT_SPECS[fmt]["label"],
                headline=brief_data.get("headline", ""),
                subline=brief_data.get("subline", ""),
                art_direction=brief_data.get("art_direction", ""),
                image_prompt=brief_data.get("image_prompt", ""),
                image_b64=img,
                storyboard_frames=None,
            ))

    print(f"[visual_director] === Done — {len(outputs)} visuals generated ===")
    for o in outputs:
        print(f"  [{o.format.value}] headline={o.headline[:40]}... has_image={o.has_image()}")

    return {
        "visuals": outputs,
        "current_step": "visualized",
    }
