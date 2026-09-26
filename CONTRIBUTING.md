# Contributing to agent-financial-analyst

## Setup
```bash
git clone https://github.com/daniellopez882/agent-financial-analyst.git
cd agent-financial-analyst
pip install -e ".[dev,all]"
pytest tests/ -v
```

## Disclaimer
This tool is for educational purposes only. Contributors should not add features that provide specific buy/sell/hold recommendations or claim to predict market movements.

## High-Impact Contributions
- **Plotly charts** — price charts, revenue bars, margin trends in HTML report
- **SEC filing RAG** — analyze 10-K/10-Q filings with retrieval
- **Earnings analysis** — parse transcripts, track beat/miss history
- **International markets** — support non-US exchanges
- **Peer comparison** — automated peer selection and comparison tables
- **FastAPI endpoint** — REST API for report generation
