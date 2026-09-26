"""Agent pipeline — 5 specialized agents for equity research."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from datetime import date
from typing import Optional

from ..models import AgentOutput, ResearchReport, StockData
from ..tools import fetch_stock_data, stock_data_summary

logger = logging.getLogger("agent-analyst")

# Cost per million tokens (March 2026)
_COST = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1-mini": (0.40, 1.60),
}


def _estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    inp_r, out_r = _COST.get(model, (2.50, 10.00))
    return (in_tok * inp_r + out_tok * out_r) / 1_000_000


async def _call_llm(
    model: str, system: str, user: str, temperature: float = 0
) -> tuple[str, int, int]:
    """Call OpenAI chat completion. Returns (content, in_tokens, out_tokens)."""
    import openai

    client = openai.AsyncOpenAI()
    resp = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    usage = resp.usage
    return (
        resp.choices[0].message.content or "",
        usage.prompt_tokens if usage else 0,
        usage.completion_tokens if usage else 0,
    )


# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------

FUNDAMENTAL_SYSTEM = """You are a senior equity research analyst specializing in fundamental analysis.
Given the financial data for a company, produce a thorough fundamental analysis covering:

1. Revenue & Growth — trend, acceleration/deceleration, drivers
2. Profitability — gross, operating, net margins; trend direction
3. Valuation — P/E, P/S, EV/EBITDA vs sector; premium/discount justification
4. Cash Flow — FCF generation, capex needs, cash conversion
5. Balance Sheet — leverage (D/E), liquidity, red flags
6. Peer Context — how metrics compare to sector medians

Use specific numbers from the data. Be balanced — note both strengths and concerns.
Format as clear Markdown with ### subheadings. Keep under 600 words.
IMPORTANT: This is for educational/research purposes only. Include no buy/sell recommendations."""

TECHNICAL_SYSTEM = """You are a technical analysis specialist.
Given price data and technical indicators, produce a technical analysis covering:

1. Trend — direction (bullish/bearish/neutral), strength, duration
2. Moving Averages — relationship to 50-day and 200-day MA
3. RSI — overbought (>70), oversold (<30), or neutral territory
4. Support & Resistance — key price levels based on recent action
5. Volume — any notable volume patterns or divergences

Use specific numbers. Be objective — technical analysis describes what IS, not what SHOULD BE.
Format as Markdown with ### subheadings. Keep under 400 words.
IMPORTANT: Educational purposes only. Not trading advice."""

RISK_SYSTEM = """You are a risk assessment specialist for equity research.
Given company data and analysis, identify and rate the key risk factors.

For each risk:
- Category (Market, Sector, Company, Regulatory, Competitive, Macro)
- Level (HIGH, MEDIUM, LOW)
- Brief description (1-2 sentences)

Identify 4-6 risk factors, prioritized by severity.
Format as a numbered Markdown list with **Category** (LEVEL): description.
Be specific to this company — no generic risks that apply to all stocks.
IMPORTANT: Educational purposes only."""

SYNTHESIS_SYSTEM = """You are a senior research report editor.
Combine the fundamental analysis, technical analysis, and risk assessment into a cohesive
executive summary and conclusion.

The executive summary should be 3-4 sentences covering: the company's position,
key financial metrics, and the primary thesis (positive and negative factors).

The conclusion should synthesize all analyses into a balanced view, noting:
- Key strengths and catalysts
- Key risks and concerns
- The overall picture for someone researching this company

Be balanced and data-driven. Do not make buy/sell/hold recommendations.
Format as Markdown. Keep each section under 300 words.
IMPORTANT: Educational/research purposes only. Not financial advice."""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class FinancialAnalyst:
    """Multi-agent financial research pipeline."""

    def __init__(
        self,
        model: str = "gpt-4o",
        fundamental_model: Optional[str] = None,
        technical_model: Optional[str] = None,
        risk_model: Optional[str] = None,
        synthesis_model: Optional[str] = None,
        output_dir: str = "reports",
        include_technicals: bool = True,
        include_risk: bool = True,
        max_news: int = 10,
    ):
        self.fundamental_model = fundamental_model or model
        self.technical_model = technical_model or "gpt-4o-mini"
        self.risk_model = risk_model or model
        self.synthesis_model = synthesis_model or model
        self.output_dir = output_dir
        self.include_technicals = include_technicals
        self.include_risk = include_risk
        self.max_news = max_news

    async def analyze(self, ticker: str) -> ResearchReport:
        """Run the full 5-agent pipeline for a ticker."""
        report = ResearchReport(
            ticker=ticker.upper(),
            date=str(date.today()),
        )
        total_cost = 0.0
        start = time.monotonic()

        # Phase 1: Market Data Agent (fetch data)
        logger.info(f"[Market Data] Fetching data for {ticker}...")
        t0 = time.monotonic()
        try:
            stock_data = fetch_stock_data(ticker, self.max_news)
            data_summary = stock_data_summary(stock_data)
            report.stock_data = stock_data

            # Build company overview from data
            report.company_overview = self._build_overview(stock_data)
        except Exception as e:
            data_summary = f"Error fetching data: {e}"
            stock_data = StockData(ticker=ticker)

        report.agent_outputs.append(AgentOutput(
            agent_name="Market Data",
            content=f"Fetched data for {ticker}",
            latency_seconds=time.monotonic() - t0,
        ))

        # Phase 2: Fundamental + Technical in parallel
        tasks = []

        # Fundamental Agent
        tasks.append(self._run_agent(
            "Fundamental",
            self.fundamental_model,
            FUNDAMENTAL_SYSTEM,
            f"Analyze the fundamentals of {ticker}:\n\n{data_summary}",
        ))

        # Technical Agent (if enabled)
        if self.include_technicals:
            tasks.append(self._run_agent(
                "Technical",
                self.technical_model,
                TECHNICAL_SYSTEM,
                f"Analyze the technicals of {ticker}:\n\n{data_summary}",
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_name = "Fundamental" if i == 0 else "Technical"
                report.agent_outputs.append(AgentOutput(
                    agent_name=agent_name, error=str(result),
                ))
            else:
                output, cost = result
                total_cost += cost
                report.agent_outputs.append(output)
                if output.agent_name == "Fundamental":
                    report.fundamental_analysis = output.content
                elif output.agent_name == "Technical":
                    report.technical_analysis = output.content

        # Phase 3: Risk Agent
        if self.include_risk:
            context = (
                f"Company: {ticker}\n\n"
                f"Data:\n{data_summary}\n\n"
                f"Fundamental Analysis:\n{report.fundamental_analysis[:1500]}"
            )
            try:
                risk_output, risk_cost = await self._run_agent(
                    "Risk", self.risk_model, RISK_SYSTEM, context,
                )
                total_cost += risk_cost
                report.agent_outputs.append(risk_output)
                report.risk_assessment = risk_output.content
            except Exception as e:
                report.agent_outputs.append(AgentOutput(
                    agent_name="Risk", error=str(e),
                ))

        # Phase 4: Synthesis Agent
        synthesis_context = (
            f"Company: {ticker}\n\n"
            f"Fundamental Analysis:\n{report.fundamental_analysis[:2000]}\n\n"
            f"Technical Analysis:\n{report.technical_analysis[:1000]}\n\n"
            f"Risk Assessment:\n{report.risk_assessment[:1000]}"
        )
        try:
            synth_output, synth_cost = await self._run_agent(
                "Synthesis", self.synthesis_model, SYNTHESIS_SYSTEM,
                synthesis_context,
            )
            total_cost += synth_cost
            report.agent_outputs.append(synth_output)

            # Parse executive summary and conclusion from synthesis
            content = synth_output.content
            if "## Conclusion" in content or "### Conclusion" in content:
                parts = re.split(r"#{2,3}\s*Conclusion", content, maxsplit=1)
                report.executive_summary = parts[0].strip()
                report.conclusion = parts[1].strip() if len(parts) > 1 else ""
            elif "## Executive Summary" in content:
                parts = content.split("## Executive Summary", 1)
                report.executive_summary = parts[1].strip() if len(parts) > 1 else content
            else:
                # Split roughly in half
                sentences = content.split(". ")
                mid = len(sentences) // 2
                report.executive_summary = ". ".join(sentences[:mid]) + "."
                report.conclusion = ". ".join(sentences[mid:])
        except Exception as e:
            report.agent_outputs.append(AgentOutput(
                agent_name="Synthesis", error=str(e),
            ))

        report.total_cost_usd = total_cost
        report.total_latency_seconds = time.monotonic() - start
        return report

    async def _run_agent(
        self, name: str, model: str, system: str, user: str
    ) -> tuple[AgentOutput, float]:
        """Run a single agent and return its output + cost."""
        logger.info(f"[{name}] Running ({model})...")
        t0 = time.monotonic()
        content, in_tok, out_tok = await _call_llm(model, system, user)
        latency = time.monotonic() - t0
        cost = _estimate_cost(model, in_tok, out_tok)

        output = AgentOutput(
            agent_name=name,
            content=content,
            latency_seconds=latency,
            tokens=in_tok + out_tok,
        )
        logger.info(f"[{name}] Done in {latency:.1f}s ({in_tok+out_tok:,} tokens)")
        return output, cost

    def _build_overview(self, data: StockData) -> str:
        """Build the company overview section from stock data."""
        from ..tools import format_number
        lines = [
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Company | {data.name} |",
            f"| Ticker | {data.ticker} |",
            f"| Sector | {data.sector} |",
            f"| Industry | {data.industry} |",
            f"| Market Cap | {format_number(data.market_cap)} |",
        ]
        if data.employees:
            lines.append(f"| Employees | {data.employees:,} |")
        if data.current_price:
            lines.append(f"| Current Price | ${data.current_price:.2f} |")

        if data.description:
            lines.append(f"\n{data.description}")

        return "\n".join(lines)
