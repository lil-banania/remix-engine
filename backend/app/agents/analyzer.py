"""Campaign Analyzer agent — decomposes a campaign into creative building blocks."""

from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
from langchain_core.messages import SystemMessage, HumanMessage

from app.models.campaign import CampaignAnalysis
from app.models.state import GraphState

SYSTEM_PROMPT = """\
You are a senior advertising strategist with 15 years of experience at top creative agencies (TBWA, Ogilvy, Wieden+Kennedy). Your job is to analyze a campaign brief and extract its creative DNA.

Given a campaign brief, decompose it into its fundamental creative building blocks:

1. **Brand & Category**: Who is speaking, in what market category
2. **Consumer Insight**: The human tension or truth the campaign exploits
3. **Creative Concept**: The central mechanism, the big idea — not the execution, the IDEA
4. **Tone of Voice**: The artistic direction, the style, the register
5. **Signature**: The campaign tagline or signature line
6. **Existing Executions**: What formats have already been produced
7. **Summary**: A one-paragraph synthesis

Be precise and strategic. Don't just describe — analyze. An insight is not "people like coffee", it's "the morning ritual is the last moment of peace before the chaos of the day."

Respond in the same language as the brief (French brief → French analysis, English brief → English analysis).
"""


def get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=MODEL,
        max_tokens=4096,
    )


async def analyze_campaign(state: GraphState) -> dict:
    """Analyze the campaign brief and extract creative building blocks."""
    llm = get_llm().with_structured_output(CampaignAnalysis)

    result = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Here is the campaign brief to analyze:\n\n{state.campaign_brief}"),
    ])

    return {
        "analysis": result,
        "current_step": "analyzed",
    }
