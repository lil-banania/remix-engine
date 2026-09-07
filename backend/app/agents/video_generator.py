"""Video Generator agent — creates 5-10s clips from generated images via Kling AI."""

from __future__ import annotations

import asyncio
import os

import httpx

# --- Configuration ---
KLING_API_KEY = os.getenv("KLING_API_KEY", "")
KLING_API_BASE = os.getenv(
    "KLING_API_BASE", "https://api.aimlapi.com"
)
KLING_MODEL = os.getenv(
    "KLING_MODEL", "klingai/video-v2-6-pro-image-to-video"
)
KLING_POLL_INTERVAL = int(os.getenv("KLING_POLL_INTERVAL", "15"))
KLING_MAX_POLLS = int(os.getenv("KLING_MAX_POLLS", "20"))  # 5 min max


async def generate_video_from_image(
    image_b64: str,
    prompt: str,
    duration: int = 5,
) -> dict:
    """Generate a short video clip from a base64 image via Kling AI.

    Args:
        image_b64: Base64-encoded source image (PNG/JPEG).
        prompt: Motion/animation prompt describing what should happen.
        duration: Clip length in seconds (5 or 10).

    Returns:
        dict with keys:
            - video_url: str | None — URL of the generated video
            - status: str — "completed" | "error" | "timeout"
            - error: str | None — error message if failed
    """
    if not KLING_API_KEY:
        return {
            "video_url": None,
            "status": "error",
            "error": "Missing KLING_API_KEY environment variable",
        }

    # Prepare the image as a data URI for the API
    image_url = f"data:image/png;base64,{image_b64}"

    payload = {
        "model": KLING_MODEL,
        "prompt": prompt,
        "image_url": image_url,
        "duration": max(5, min(duration, 10)),
        "negative_prompt": "blurry, distorted text, low quality, watermark",
        "generate_audio": False,
    }

    headers = {
        "Authorization": f"Bearer {KLING_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"[video_generator] Submitting video generation — model={KLING_MODEL}, duration={duration}s")

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Submit generation task
        try:
            resp = await client.post(
                f"{KLING_API_BASE}/v2/video/generations",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"Kling API error: {e.response.status_code} — {e.response.text[:200]}"
            print(f"[video_generator] {error_msg}")
            return {"video_url": None, "status": "error", "error": error_msg}
        except Exception as e:
            error_msg = f"Kling API request failed: {e}"
            print(f"[video_generator] {error_msg}")
            return {"video_url": None, "status": "error", "error": error_msg}

        generation_id = result.get("id")
        if not generation_id:
            return {
                "video_url": None,
                "status": "error",
                "error": f"No generation ID returned: {result}",
            }

        print(f"[video_generator] Task queued — id={generation_id}")

        # Step 2: Poll for completion
        for attempt in range(KLING_MAX_POLLS):
            await asyncio.sleep(KLING_POLL_INTERVAL)

            try:
                poll_resp = await client.get(
                    f"{KLING_API_BASE}/v2/video/generations",
                    params={"generation_id": generation_id},
                    headers=headers,
                )
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()
            except Exception as e:
                print(f"[video_generator] Poll error (attempt {attempt+1}): {e}")
                continue

            status = poll_data.get("status", "unknown")
            print(f"[video_generator] Poll {attempt+1}/{KLING_MAX_POLLS} — status={status}")

            if status == "completed":
                video_url = None
                video_data = poll_data.get("video")
                if video_data and isinstance(video_data, dict):
                    video_url = video_data.get("url")
                elif isinstance(poll_data.get("artifacts"), list):
                    # Some API wrappers return artifacts list
                    for artifact in poll_data["artifacts"]:
                        if artifact.get("video"):
                            video_url = artifact["video"]
                            break

                print(f"[video_generator] Video ready — url={video_url[:80] if video_url else 'None'}...")
                return {
                    "video_url": video_url,
                    "status": "completed",
                    "error": None,
                }

            elif status == "error":
                error_info = poll_data.get("error", {})
                error_msg = error_info.get("message", "Unknown error") if isinstance(error_info, dict) else str(error_info)
                print(f"[video_generator] Generation failed: {error_msg}")
                return {
                    "video_url": None,
                    "status": "error",
                    "error": error_msg,
                }

        # Timeout
        print(f"[video_generator] Timeout after {KLING_MAX_POLLS * KLING_POLL_INTERVAL}s")
        return {
            "video_url": None,
            "status": "timeout",
            "error": f"Video generation timed out after {KLING_MAX_POLLS * KLING_POLL_INTERVAL}s",
        }
