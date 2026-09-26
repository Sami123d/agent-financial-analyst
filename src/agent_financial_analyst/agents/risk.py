"""Risk Assessment Agent."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..core.base import BaseAgent
from ..schema.models import RiskFactor, RiskLevel


class RiskAgent(BaseAgent):
    """
    Agent specializing in identifying and rating market, sector, and company risks.
    """

    def __init__(self, model: str = "gpt-4o"):
        super().__init__(agent_id="risk_analyst", model=model)

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return (
            "You are a risk assessment specialist for institutional equity research. "
            "You are tasked with identifying and prioritizing the critical risks "
            "for a given stock. You should analyze market, sector, company, and "
            "regulatory risks. For each risk, specify its category, its level "
            "(HIGH, MEDIUM, LOW), a brief title, and its description. Respond "
            "in a structured JSON format to allow integration into larger reports."
        )

    async def analyze(self, ticker: str, data_context: str) -> List[RiskFactor]:
        """Run the risk assessment and return structured risk factors."""
        user_prompt = (
            f"Identify the top 4-6 risk factors for {ticker} using the provided market "
            f"data and context. Here is the raw data:\n\n{data_context}\n\n"
            "Return only a JSON list of risk objects, for example:\n"
            '[{"category": "Regulatory", "level": "HIGH", "title": "...", "description": "..."}]'
        )
        
        output = await self.run(user_prompt)
        
        try:
            # Simple extractor for markdown json blocks or raw json
            json_str = output.content
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            
            raw_risks = json.loads(json_str)
            return [RiskFactor(**r) for r in raw_risks]
        except Exception as e:
            self.log_thought(step="risk_parsing_failed", reasoning=f"Fallback to default risk factor due to error: {e}")
            return [RiskFactor(
                category="General",
                level=RiskLevel.MEDIUM,
                title="Generic Risk",
                description="Unable to parse detailed risk report. External risk assessment recommended.",
            )]
