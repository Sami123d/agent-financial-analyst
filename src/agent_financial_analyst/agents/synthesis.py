"""Synthesis Specialist Agent."""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from ..core.base import BaseAgent


class SynthesisAgent(BaseAgent):
    """
    Agent responsible for combining individual analyst findings into a 
    cohesive institutional report.
    """

    def __init__(self, model: str = "gpt-4o"):
        super().__init__(agent_id="synthesis_specialist", model=model)

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return (
            "You are a senior equity research board member. Your task is to "
            "synthesize detailed analyses from several specialist agents into a "
            "consolidated, professional research report for institutional "
            "investors. Your report should highlight the critical findings, "
            "balance competing data points, and provide a clear, one-page summary "
            "followed by a detailed conclusion. Do not make buy/sell recommendations."
        )

    async def summarize(self, ticker: str, fundamental: str, technical: str, risks: str) -> Tuple[str, str]:
        """Produce the executive summary and overall conclusion."""
        user_prompt = (
            f"Synthesize the research for {ticker}. Combine the following specialist "
            f"analyses into a cohesive whole:\n\n"
            f"### FUNDAMENTAL ANALYSIS\n{fundamental}\n\n"
            f"### TECHNICAL ANALYSIS\n{technical}\n\n"
            f"### RISK ASSESSMENT\n{risks}\n\n"
            "Format your output as follows:\n"
            "1. EXECUTIVE SUMMARY: A paragraph (3-4 sentences) summarizing the key takeaways.\n"
            "2. THE CONSOLIDATED THESIS: A summary detailing the primary catalysts and risks.\n"
            "3. FINAL CONCLUSION: The closing statement for this equity report."
        )
        
        output = await self.run(user_prompt)
        content = output.content
        
        # Simple extraction for demo:
        summary_sections = content.split("##")
        if len(summary_sections) > 1:
            return summary_sections[1].strip(), content
        
        return content[:400], content
