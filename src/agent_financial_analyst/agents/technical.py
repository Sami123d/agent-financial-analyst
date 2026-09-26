"""Technical Specialist Agent."""

from __future__ import annotations

from typing import Any, Dict

from ..core.base import BaseAgent


class TechnicalAgent(BaseAgent):
    """
    Agent specializing in price action and technical indicators.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(agent_id="technical_analyst", model=model)

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return (
            "You are a technical analysis specialist. Your role is to analyze a "
            "stock's price action, trend direction, moving averages, and momentum "
            "indicators like RSI. You should identify key support and resistance "
            "levels based on recent history. Be objective and describe what the "
            "data shows, not what you think should happen. This analysis should be "
            "grounded in actual historical data, not speculation. "
        )

    async def analyze(self, ticker: str, data_context: str) -> str:
        """Run technical analysis based on provided market data."""
        user_prompt = (
            f"As a technical analyst, analyze the performance of {ticker}. "
            f"Here is the raw data available:\n\n{data_context}\n\n"
            "Focus your analysis on:\n"
            "1. Price Trend (Short vs Long Term)\n"
            "2. Moving Average Crossovers (50-day and 200-day)\n"
            "3. RSI and MACD (Momentum indicators)\n"
            "4. Support and Resistance levels."
        )
        output = await self.run(user_prompt)
        return output.content
