"""Core data models for agent-financial-analyst.

DEPRECATION WARNING: This module contains legacy dataclass models. 
New code should use the modernized Pydantic V2 models in `schema/models.py`.
Kept for backward compatibility and legacy CLI tools (summary, fundamentals, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class RiskLevel(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class StockData:
    """Raw market data for a ticker."""

    ticker: str
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    employees: int = 0
    description: str = ""

    # Price
    current_price: float = 0.0
    price_change_pct: float = 0.0
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0
    avg_volume: int = 0
    beta: float = 0.0

    # Fundamentals
    revenue_ttm: float = 0.0
    revenue_growth: float = 0.0
    gross_margin: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0
    eps: float = 0.0
    pe_ratio: float = 0.0
    forward_pe: float = 0.0
    ps_ratio: float = 0.0
    pb_ratio: float = 0.0
    ev_ebitda: float = 0.0
    free_cash_flow: float = 0.0
    debt_to_equity: float = 0.0
    roe: float = 0.0
    dividend_yield: float = 0.0

    # Technical (computed)
    sma_50: float = 0.0
    sma_200: float = 0.0
    rsi_14: float = 0.0
    above_50ma: bool = False
    above_200ma: bool = False

    # News
    news: list[dict] = field(default_factory=list)
    price_history: list[dict] = field(default_factory=list)


@dataclass
class AgentOutput:
    """Output from a single agent in the pipeline."""

    agent_name: str
    content: str = ""
    latency_seconds: float = 0.0
    tokens: int = 0
    error: Optional[str] = None


@dataclass
class RiskFactor:
    """A single risk factor identified by the risk agent."""

    category: str
    level: RiskLevel
    description: str


@dataclass
class ResearchReport:
    """Complete equity research report."""

    ticker: str
    date: str = ""
    executive_summary: str = ""
    company_overview: str = ""
    fundamental_analysis: str = ""
    technical_analysis: str = ""
    risk_assessment: str = ""
    conclusion: str = ""
    agent_outputs: list[AgentOutput] = field(default_factory=list)
    stock_data: Optional[StockData] = None
    total_cost_usd: float = 0.0
    total_latency_seconds: float = 0.0

    @property
    def markdown(self) -> str:
        """Render the full report as Markdown."""
        sections = [
            f"# {self.ticker} — Equity Research Report",
            f"*Generated {self.date} by agent-financial-analyst*",
            "",
            f"## Executive Summary\n{self.executive_summary}",
        ]

        if self.company_overview:
            sections.append(f"\n## Company Overview\n{self.company_overview}")
        if self.fundamental_analysis:
            sections.append(f"\n## Fundamental Analysis\n{self.fundamental_analysis}")
        if self.technical_analysis:
            sections.append(f"\n## Technical Analysis\n{self.technical_analysis}")
        if self.risk_assessment:
            sections.append(f"\n## Risk Assessment\n{self.risk_assessment}")
        if self.conclusion:
            sections.append(f"\n## Conclusion\n{self.conclusion}")

        sections.append(
            f"\n---\n*Report generated in {self.total_latency_seconds:.1f}s "
            f"| Cost: ${self.total_cost_usd:.3f} "
            f"| Disclaimer: This is AI-generated analysis for educational "
            f"purposes only. Not financial advice.*"
        )
        return "\n".join(sections)

    def save(self, output_dir: str = "reports") -> Path:
        """Save the report as a Markdown file."""
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        filepath = path / f"{self.ticker}_report.md"
        filepath.write_text(self.markdown)
        return filepath

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "date": self.date,
            "sections": {
                "executive_summary": self.executive_summary,
                "company_overview": self.company_overview,
                "fundamental_analysis": self.fundamental_analysis,
                "technical_analysis": self.technical_analysis,
                "risk_assessment": self.risk_assessment,
                "conclusion": self.conclusion,
            },
            "meta": {
                "total_latency_s": round(self.total_latency_seconds, 1),
                "total_cost_usd": round(self.total_cost_usd, 4),
                "agents": [
                    {
                        "name": a.agent_name,
                        "latency_s": round(a.latency_seconds, 1),
                        "tokens": a.tokens,
                        "error": a.error,
                    }
                    for a in self.agent_outputs
                ],
            },
        }
