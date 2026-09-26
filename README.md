<div align="center">

# agent-financial-analyst

**Multi-agent equity research, automated.**

Five specialized AI agents collaborate to produce institutional-grade research reports:
Market Data → Fundamental Analysis → Technical Analysis → Risk Assessment → Report Synthesis.

One command: `agent-analyst report NVDA`

[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue?style=flat-square)](https://pypi.org/project/agent-financial-analyst/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)

[Quick Start](#-quick-start) · [Agent Pipeline](#-agent-pipeline) · [Report Sample](#-sample-output) · [CLI](#-cli)

</div>

---

## ⚠️ Disclaimer

**This tool is for educational and research purposes only.** It does not constitute financial advice, investment recommendations, or solicitations. AI-generated analysis can contain errors, hallucinations, and outdated information. Always consult qualified financial professionals before making investment decisions. Past performance does not guarantee future results.

---

## 🔥 The Problem

Professional equity research costs $24,000+/year (Bloomberg Terminal) or requires teams of analysts spending days per report. Existing AI tools are either:

- **Academic frameworks** (FinRobot) — Complex setup, AutoGen dependencies, research-focused
- **Trading bots** (TradingAgents) — Trading decisions, not research reports
- **Single-agent chatbots** — Ask GPT about a stock, get a generic paragraph

**agent-financial-analyst** is different: 5 specialized agents collaborate in a pipeline that mirrors how a real research desk operates. Each agent has domain-specific tools and instructions. The output is a structured, data-backed Markdown report — not a chatbot response.

---

## ⚡ Quick Start

### Install

```bash
pip install agent-financial-analyst
```

### Generate a report

```bash
export OPENAI_API_KEY=sk-...
agent-analyst report NVDA
```

**Output:** A complete equity research report saved to `reports/NVDA_report.md`

```
agent-financial-analyst v0.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Market Data Agent       │  3.2s │ fetched price, financials, news
  ✅ Fundamental Agent       │  5.1s │ revenue, margins, valuation
  ✅ Technical Agent         │  2.8s │ trend, RSI, support/resistance
  ✅ Risk Agent              │  3.4s │ 6 risk factors identified
  ✅ Synthesis Agent         │  4.7s │ report compiled
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total: 19.2s │ $0.14 │ 📄 reports/NVDA_report.md
```

---

## 🧬 Agent Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  USER INPUT: "NVDA"                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  MARKET DATA    │  Tools: yfinance, news API
              │  AGENT          │  Fetches: price history, financials,
              │                 │  earnings, news headlines, sector data
              └────────┬────────┘
                       │
           ┌───────────┼───────────┐
           ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  FUNDAMENTAL     │    │  TECHNICAL       │
│  AGENT           │    │  AGENT           │
│                  │    │                  │
│  • Revenue trend │    │  • Price trend   │
│  • Margin anal.  │    │  • RSI / MACD    │
│  • P/E, P/S, EV │    │  • Support/Res.  │
│  • FCF analysis  │    │  • Volume anal.  │
│  • Peer compare  │    │  • Moving avg.   │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
           ┌──────────────────┐
           │  RISK ASSESSMENT │
           │  AGENT           │
           │                  │
           │  • Market risk   │
           │  • Sector risk   │
           │  • Company risk  │
           │  • Regulatory    │
           │  • Competitive   │
           │  • Macro factors │
           └────────┬─────────┘
                    ▼
           ┌──────────────────┐
           │  SYNTHESIS       │
           │  AGENT           │
           │                  │
           │  Combines all    │
           │  analyses into   │
           │  a structured    │
           │  research report │
           │  with conclusion │
           └────────┬─────────┘
                    ▼
            📄 NVDA_report.md
```

### Why 5 Agents Instead of 1?

The research is clear: multi-agent systems outperform single agents on complex financial analysis. FinRobot's experiments on Dow Jones 30 companies showed multi-agent collaboration structures improve analysis accuracy, especially when agents have specialized roles and tools. Our pipeline mirrors how real research desks operate: data collection → fundamental analysis → technical analysis → risk assessment → synthesis.

---

## 📊 Sample Output

The report follows institutional standards:

```markdown
# NVDA — Equity Research Report
*Generated 2026-03-31 by agent-financial-analyst*

## Executive Summary
NVIDIA Corporation shows strong revenue momentum driven by data center
demand, with Q4 FY2025 revenue of $39.3B (+78% YoY). Valuation remains
elevated at 45x forward P/E vs sector median 28x...

## Company Overview
| Metric          | Value        |
|----------------|-------------|
| Market Cap     | $3.42T       |
| Sector         | Technology   |
| Industry       | Semiconductors |
| Employees      | 32,112       |

## Fundamental Analysis
### Revenue & Growth
- TTM Revenue: $130.5B (+114% YoY)
- Gross Margin: 73.0% (expanding from 64.6%)
- Operating Margin: 62.3%
- Free Cash Flow: $60.9B

### Valuation
| Metric     | NVDA   | Sector Median |
|-----------|--------|--------------|
| P/E (Fwd) | 45.2x  | 28.1x        |
| P/S       | 26.2x  | 5.8x         |
| EV/EBITDA | 38.7x  | 18.2x        |

## Technical Analysis
- Trend: Bullish (above 50-day and 200-day MA)
- RSI (14): 62.3 (neutral, approaching overbought)
- Support: $118.50 │ Resistance: $142.80
- Volume: Above 20-day average

## Risk Factors
1. **Valuation Risk** (HIGH) — Premium valuation leaves limited
   margin of safety...
2. **Concentration Risk** (MEDIUM) — Data center segment = 83%
   of revenue...
3. **Geopolitical Risk** (MEDIUM) — Export restrictions to China...
...

## Conclusion
[Agent synthesizes all findings into investment thesis]
```

---

## 🖥️ CLI

```bash
# Generate a full research report
agent-analyst report NVDA
agent-analyst report AAPL --model gpt-4o
agent-analyst report MSFT --output reports/msft.md

# Quick summary (no full report)
agent-analyst summary TSLA

# Compare two stocks
agent-analyst compare NVDA AMD

# Fundamental data only
agent-analyst fundamentals GOOGL

# Technical analysis only
agent-analyst technicals META

# Batch: analyze a watchlist
agent-analyst batch watchlist.txt --output-dir reports/
```

---

## 📐 Architecture

### Data Sources (via yfinance + web)

| Data | Source | Agent |
|------|--------|-------|
| Price history | yfinance | Market Data |
| Financial statements | yfinance | Market Data |
| Key ratios | yfinance | Market Data |
| Earnings data | yfinance | Market Data |
| Company info | yfinance | Market Data |
| News headlines | yfinance/web | Market Data |
| Sector peers | yfinance | Fundamental |

### Agent Specializations

| Agent | Model | Role | Output |
|-------|-------|------|--------|
| **Market Data** | gpt-4o-mini | Fetch and structure raw data | JSON with all data points |
| **Fundamental** | gpt-4o | Analyze financials, valuation, peers | Fundamental analysis section |
| **Technical** | gpt-4o-mini | Analyze price action, indicators | Technical analysis section |
| **Risk** | gpt-4o | Identify and rate risk factors | Prioritized risk table |
| **Synthesis** | gpt-4o | Combine all analyses into report | Final Markdown report |

### Model Tiering

Expensive models (gpt-4o) are used only where judgment matters: fundamental analysis, risk assessment, and final synthesis. Cheaper models (gpt-4o-mini) handle data fetching and technical pattern recognition. This keeps cost under $0.15 per report.

---

## 🔌 Configuration

```python
from agent_financial_analyst import FinancialAnalyst

analyst = FinancialAnalyst(
    model="gpt-4o",                    # Override all agents to same model
    fundamental_model="gpt-4o",        # Per-agent model override
    technical_model="gpt-4o-mini",
    risk_model="gpt-4o",
    synthesis_model="gpt-4o",
    output_dir="reports/",
    include_technicals=True,           # Toggle sections
    include_risk=True,
    max_news=10,                       # News headlines to fetch
)

report = await analyst.analyze("NVDA")
print(report.markdown)
report.save()                          # Saves to reports/NVDA_report.md
```

---

## 🆚 How This Compares

| Tool | Agents | CLI | Free | Report Quality | Setup |
|------|:------:|:---:|:----:|:-----------:|-------|
| **agent-financial-analyst** | 5 specialized | ✅ | ✅ | Institutional-grade | `pip install` |
| FinRobot | 3 CoT | ❌ | ✅ | Academic | Complex (AutoGen) |
| TradingAgents | Multi | ❌ | ✅ | Trading signals | Moderate |
| Dexter | 1 | ❌ | ✅ | Conversational | TypeScript |
| Bloomberg Terminal | N/A | N/A | ❌ ($24K/yr) | Gold standard | Enterprise |

**The differentiator:** One command, structured Markdown output, model-tiered for cost efficiency, designed as a portfolio showcase for multi-agent engineering.

---

## 🗺️ Roadmap

- [x] 5-agent pipeline with specialized roles
- [x] yfinance data integration
- [x] Structured Markdown report output
- [x] Model tiering for cost efficiency
- [x] CLI with Rich progress output
- [ ] Plotly charts embedded in HTML report
- [ ] SEC 10-K/10-Q filing analysis (RAG)
- [ ] Earnings call transcript analysis
- [ ] Peer comparison tables
- [ ] Portfolio-level analysis
- [ ] FastAPI REST endpoint
- [ ] Watchlist batch processing
- [ ] Historical report diffing

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

**High-impact contributions:**
- **Chart generation** — Plotly price charts, revenue bars, margin trends
- **SEC filing integration** — RAG over 10-K/10-Q filings
- **Earnings analysis** — Transcript parsing, beat/miss tracking
- **International markets** — Support for non-US exchanges
- **Alternative data** — Reddit sentiment, options flow, insider trading

---

## License

[MIT](LICENSE) — Analyze responsibly.

<div align="center">

**[agent-financial-analyst](https://github.com/daniellopez882/agent-financial-analyst)** by [Ismail Sajid](https://github.com/Ismail-2001/)

*Five agents. One report. Zero terminal fees.*

</div>

## Attribution
This repository is an unmodified copy of [Ismail-2001/agent-financial-analyst](https://github.com/Ismail-2001/agent-financial-analyst), imported on 2026-09-27. No code changes have been made yet.
The code is licensed under the MIT License. The LICENSE file and its copyright notice ("Copyright (c) 2026 Daniel López Orta") are preserved unchanged.
The upstream repository's commit history lists Daniel Lopez and Ismail Sajid as authors. That history was not carried over into this import; see the upstream repository for it.
Imported and maintained by [Sami123d](https://github.com/Sami123d). Any future changes will be listed under "Changes in this repository" below.
