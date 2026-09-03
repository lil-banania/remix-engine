"""FastAPI server for the Remix Engine."""

from __future__ import annotations

import json
import os
import asyncio
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.models.campaign import (
    CampaignAnalysis,
    FORMAT_SPECS,
    RemixFormat,
    RemixResult,
)
from app.models.visuals import VisualFormat, VisualOutput, VISUAL_FORMAT_SPECS
from app.models.state import GraphState
from app.graph import remix_graph

load_dotenv()

app = FastAPI(
    title="Remix Engine",
    description="Feed it a campaign. Get it everywhere.",
    version="1.1.0",
)

# CORS: allow frontend origin (Vercel in prod, localhost in dev)
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response models ---

class AnalyzeRequest(BaseModel):
    campaign_brief: str = Field(
        min_length=50,
        description="The campaign brief to analyze (at least 50 characters)",
    )


class AnalyzeResponse(BaseModel):
    analysis: CampaignAnalysis


class RemixRequestBody(BaseModel):
    campaign_brief: str = Field(min_length=50)
    formats: list[RemixFormat] = Field(min_length=1, max_length=5)
    target_audience: Optional[str] = None
    target_market: Optional[str] = None
    visual_formats: list[VisualFormat] = Field(
        default_factory=list,
        description="Visual formats to generate (empty = skip visuals)",
    )


class RemixResponse(BaseModel):
    analysis: CampaignAnalysis
    results: list[RemixResult]
    visuals: list[dict] = Field(default_factory=list)


class FormatInfo(BaseModel):
    key: str
    label: str
    duration: str
    aspect_ratio: str
    constraints: str


class VisualFormatInfo(BaseModel):
    key: str
    label: str
    aspect_ratio: str
    description: str


class VisualsRequest(BaseModel):
    """Standalone request to generate visuals for an existing remix."""
    campaign_brief: str = Field(min_length=50)
    visual_formats: list[VisualFormat] = Field(min_length=1, max_length=4)


# --- Routes ---

@app.get("/")
async def root():
    return {
        "name": "Remix Engine",
        "tagline": "Feed it a campaign. Get it everywhere.",
        "version": "1.1.0",
        "features": ["remix", "visual_director"],
    }


@app.get("/formats", response_model=list[FormatInfo])
async def list_formats():
    """List all available remix formats with their specs."""
    return [
        FormatInfo(key=fmt.value, **specs)
        for fmt, specs in FORMAT_SPECS.items()
    ]


@app.get("/visual-formats", response_model=list[VisualFormatInfo])
async def list_visual_formats():
    """List available visual generation formats."""
    return [
        VisualFormatInfo(key=fmt.value, **specs)
        for fmt, specs in VISUAL_FORMAT_SPECS.items()
    ]


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """Step 1: Analyze a campaign brief into creative building blocks."""
    state = GraphState(campaign_brief=req.campaign_brief)

    # Run only the analyze node
    from app.agents.analyzer import analyze_campaign
    result = await analyze_campaign(state)

    if not result.get("analysis"):
        raise HTTPException(500, "Failed to analyze campaign")

    return AnalyzeResponse(analysis=result["analysis"])


@app.post("/remix", response_model=RemixResponse)
async def remix(req: RemixRequestBody):
    """Run the full remix pipeline: analyze -> scenarios -> plan -> write -> check [-> visual_direct]."""
    from app.models.campaign import RemixRequest

    initial_state = GraphState(
        campaign_brief=req.campaign_brief,
        remix_request=RemixRequest(
            formats=req.formats,
            target_audience=req.target_audience,
            target_market=req.target_market,
        ),
        visual_formats=req.visual_formats,
    )

    # Run the full graph
    final_state = await remix_graph.ainvoke(initial_state)

    if final_state.get("error"):
        raise HTTPException(500, final_state["error"])

    visuals = final_state.get("visuals", [])
    return RemixResponse(
        analysis=final_state["analysis"],
        results=final_state["results"],
        visuals=[v.to_api_dict() for v in visuals] if visuals else [],
    )


@app.post("/remix/stream")
async def remix_stream(req: RemixRequestBody):
    """Stream the remix pipeline with SSE progress events."""
    from app.models.campaign import RemixRequest

    initial_state = GraphState(
        campaign_brief=req.campaign_brief,
        remix_request=RemixRequest(
            formats=req.formats,
            target_audience=req.target_audience,
            target_market=req.target_market,
        ),
        visual_formats=req.visual_formats,
    )

    async def event_generator():
        async for event in remix_graph.astream(
            initial_state,
            stream_mode="updates",
        ):
            for node_name, node_output in event.items():
                step = node_output.get("current_step", node_name)

                # Build a serializable payload
                payload = {"step": step, "node": node_name}

                # Forward errors from any node
                if node_output.get("error"):
                    payload["error"] = node_output["error"]

                if node_name == "analyze" and node_output.get("analysis"):
                    payload["analysis"] = node_output["analysis"].model_dump()

                if node_name == "scenarios" and node_output.get("scenarios"):
                    payload["scenarios"] = [
                        s.model_dump() for s in node_output["scenarios"]
                    ]

                if node_name == "check" and node_output.get("results"):
                    payload["results"] = [
                        r.model_dump() for r in node_output["results"]
                    ]

                if node_name == "check" and node_output.get("scenario_results"):
                    payload["scenario_results"] = [
                        sr.model_dump() for sr in node_output["scenario_results"]
                    ]

                if node_name == "visual_direct" and node_output.get("visuals"):
                    try:
                        visuals_list = node_output["visuals"]
                        payload["visuals"] = [
                            v.to_api_dict() if hasattr(v, "to_api_dict") else v
                            for v in visuals_list
                        ]
                    except Exception as e:
                        print(f"[SSE] Error serializing visuals: {e}")
                        payload["error"] = f"Visual serialization failed: {e}"

                yield {
                    "event": "progress",
                    "data": json.dumps(payload, default=str),
                }

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())


@app.post("/visuals/generate")
async def generate_visuals_standalone(req: VisualsRequest):
    """Standalone visual generation -- runs analyze + visual_direct only.

    Use this to (re-)generate visuals separately from the text remix pipeline.
    """
    from app.agents.analyzer import analyze_campaign
    from app.agents.visual_director import generate_visuals

    state = GraphState(
        campaign_brief=req.campaign_brief,
        visual_formats=req.visual_formats,
    )

    # Step 1: Analyze
    analysis_result = await analyze_campaign(state)
    if not analysis_result.get("analysis"):
        raise HTTPException(500, "Failed to analyze campaign")

    state.analysis = analysis_result["analysis"]

    # Step 2: Generate visuals
    visuals_result = await generate_visuals(state)
    if visuals_result.get("error"):
        raise HTTPException(500, visuals_result["error"])

    visuals = visuals_result.get("visuals", [])

    return {
        "analysis": state.analysis.model_dump(),
        "visuals": [v.to_api_dict() for v in visuals],
    }
