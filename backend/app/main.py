"""FastAPI server for the Remix Engine."""

from __future__ import annotations

import json
import asyncio
from typing import Optional

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
from app.models.state import GraphState
from app.graph import remix_graph


app = FastAPI(
    title="Remix Engine",
    description="Feed it a campaign. Get it everywhere.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


class RemixResponse(BaseModel):
    analysis: CampaignAnalysis
    results: list[RemixResult]


class FormatInfo(BaseModel):
    key: str
    label: str
    duration: str
    aspect_ratio: str
    constraints: str


# --- Routes ---

@app.get("/")
async def root():
    return {
        "name": "Remix Engine",
        "tagline": "Feed it a campaign. Get it everywhere.",
        "version": "1.0.0",
    }


@app.get("/formats", response_model=list[FormatInfo])
async def list_formats():
    """List all available remix formats with their specs."""
    return [
        FormatInfo(key=fmt.value, **specs)
        for fmt, specs in FORMAT_SPECS.items()
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
    """Run the full remix pipeline: analyze → plan → write → check."""
    from app.models.campaign import RemixRequest

    initial_state = GraphState(
        campaign_brief=req.campaign_brief,
        remix_request=RemixRequest(
            formats=req.formats,
            target_audience=req.target_audience,
            target_market=req.target_market,
        ),
    )

    # Run the full graph
    final_state = await remix_graph.ainvoke(initial_state)

    if final_state.get("error"):
        raise HTTPException(500, final_state["error"])

    return RemixResponse(
        analysis=final_state["analysis"],
        results=final_state["results"],
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

                if node_name == "analyze" and node_output.get("analysis"):
                    payload["analysis"] = node_output["analysis"].model_dump()

                if node_name == "check" and node_output.get("results"):
                    payload["results"] = [
                        r.model_dump() for r in node_output["results"]
                    ]

                yield {
                    "event": "progress",
                    "data": json.dumps(payload, default=str),
                }

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())
