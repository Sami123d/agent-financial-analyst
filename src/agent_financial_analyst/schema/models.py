"""Pydantic V2 schemas for agent-financial-analyst."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"


class StockMetadata(BaseModel):
    """Basic company identity data."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g. NVDA)")
    name: str = Field(default="", description="Full company name")
    sector: str = Field(default="", description="GICS Sector category")
    industry: str = Field(default="", description="Industry group")
    market_cap: float = Field(default=0.0, description="Total market capitalization in USD")
    employees: Optional[int] = Field(default=None, description="Number of full-time employees")
    description: Optional[str] = Field(default=None, description="Company business summary")


class ValuationMetrics(BaseModel):
    """Core financial valuation ratios."""
    pe_ratio: Optional[float] = Field(default=None, alias="trailingPE")
    forward_pe: Optional[float] = Field(default=None, alias="forwardPE")
    ps_ratio: Optional[float] = Field(default=None, alias="priceToSalesTrailing12Months")
    pb_ratio: Optional[float] = Field(default=None, alias="priceToBook")
    ev_ebitda: Optional[float] = Field(default=None, alias="enterpriseToEbitda")
    dividend_yield: Optional[float] = Field(default=None, alias="dividendYield")

    class Config:
        populate_by_name = True


class FinancialGrowth(BaseModel):
    """Historical growth metrics."""
    revenue_ttm: float = Field(default=0.0)
    revenue_growth_yoy: float = Field(default=0.0)
    gross_margin: float = Field(default=0.0)
    operating_margin: float = Field(default=0.0)
    net_margin: float = Field(default=0.0)
    free_cash_flow: float = Field(default=0.0)
    debt_to_equity: float = Field(default=0.0)
    roe: float = Field(default=0.0)


class PriceAction(BaseModel):
    """Current price and technical indicators."""
    current_price: float
    price_change_1d_pct: float = 0.0
    fifty_two_week_high: float
    fifty_two_week_low: float
    avg_volume: int
    beta: float = 1.0
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    rsi_14: Optional[float] = None


class Article(BaseModel):
    """A news headline or summary."""
    title: str
    link: str
    published_at: datetime
    publisher: str
    summary: Optional[str] = None


class MarketDataState(BaseModel):
    """Consolidated state from the Market Data Agent."""
    metadata: StockMetadata
    valuation: ValuationMetrics
    growth: FinancialGrowth
    price: PriceAction
    news: List[Article] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentThought(BaseModel):
    """Internal monologue or reasoning step from an agent."""
    step: str
    reasoning: str
    tool_used: Optional[str] = None
    observation: Optional[str] = None


class AgentOutput(BaseModel):
    """Structured output from a specific agent."""
    agent_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    thoughts: List[AgentThought] = Field(default_factory=list)
    latency_ms: float
    tokens_prompt: int
    tokens_completion: int
    cost_usd: float = 0.0

    @property
    def agent_name(self) -> str:
        return self.agent_id.replace("_", " ").title()

    @property
    def error(self) -> Optional[str]:
        return self.metadata.get("error")

    @property
    def latency_seconds(self) -> float:
        return self.latency_ms / 1000.0

    @property
    def tokens(self) -> int:
        return self.tokens_prompt + self.tokens_completion


class RiskFactor(BaseModel):
    """A specific risk identified by the Risk Agent."""
    category: str
    level: RiskLevel
    title: str
    description: str
    mitigation: Optional[str] = None


class ResearchReport(BaseModel):
    """The final institutional-grade research product."""
    task_id: str
    ticker: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    executive_summary: str
    company_context: str
    fundamental_analysis: str
    technical_analysis: str
    risk_assessment: List[RiskFactor]
    conclusion: str
    
    data_snapshot: MarketDataState
    agent_traces: List[AgentOutput]
    
    total_latency_ms: float
    total_cost_usd: float

    @property
    def agent_outputs(self) -> List[AgentOutput]:
        return self.agent_traces

    @property
    def total_latency_seconds(self) -> float:
        return self.total_latency_ms / 1000.0

    @property
    def summary_markdown(self) -> str:
        """Render a concise summary of the report."""
        return f"# {self.ticker} Analysis\n\n{self.executive_summary}"

    @property
    def markdown(self) -> str:
        """Render the full report as Markdown."""
        date_str = self.created_at.strftime("%Y-%m-%d")
        sections = [
            f"# {self.ticker} — Equity Research Report",
            f"*Generated {date_str} by agent-financial-analyst*",
            "",
            f"## Executive Summary\n{self.executive_summary}",
        ]

        if self.company_context:
            sections.append(f"\n## Company Overview\n{self.company_context}")
        if self.fundamental_analysis:
            sections.append(f"\n## Fundamental Analysis\n{self.fundamental_analysis}")
        if self.technical_analysis:
            sections.append(f"\n## Technical Analysis\n{self.technical_analysis}")
        if self.risk_assessment:
            risk_text = "\n".join([f"- **{r.category}** ({r.level.value}): {r.description}" for r in self.risk_assessment])
            sections.append(f"\n## Risk Assessment\n{risk_text}")
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
        """Compatibility dict converter."""
        date_str = self.created_at.strftime("%Y-%m-%d")
        return {
            "ticker": self.ticker,
            "date": date_str,
            "sections": {
                "executive_summary": self.executive_summary,
                "company_overview": self.company_context,
                "fundamental_analysis": self.fundamental_analysis,
                "technical_analysis": self.technical_analysis,
                "risk_assessment": "\n".join([f"- **{r.category}** ({r.level.value}): {r.description}" for r in self.risk_assessment]),
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

