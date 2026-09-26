"""Fundamental Specialist Agent."""

from __future__ import annotations

from typing import Any, Dict

from ..core.base import BaseAgent


class FundamentalAgent(BaseAgent):
    """
    Agent specializing in senior equity research-level fundamental analysis.
    """

    def __init__(self, model: str = "gpt-4o"):
        super().__init__(agent_id="fundamental_analyst", model=model)

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return (
            "You are a senior equity research analyst specializing in fundamental analysis. "
            "You are tasked with analyzing a company's revenue trends, margins, valuation, "
            "and balance sheet strength. Your analysis must be data-driven, balanced, and "
            "focused on both core strengths and material concerns. Use institutional-grade "
            "financial terminology. Do not make buy/sell recommendations."
        )

    async def analyze(self, ticker: str, data_context: str) -> str:
        """Run the analysis based on provided market data."""
        user_prompt = (
            f"Produce a comprehensive fundamental analysis for {ticker}. "
            f"Here is the raw data available:\n\n{data_context}\n\n"
            "Focus your analysis on:\n"
            "1. Revenue and Earnings Growth\n"
            "2. Margin Expansion / Contraction\n"
            "3. Valuation Comparatives (P/E, EV/EBITDA)\n"
            "4. Cash Flow and Core Quality of Earnings"
        )
        output = await self.run(user_prompt)
        return output.content
