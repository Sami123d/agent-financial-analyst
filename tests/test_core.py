"""Comprehensive tests for agent-financial-analyst."""

import os
os.environ["OPENAI_API_KEY"] = "mock-key-for-unit-testing"

import json
from pathlib import Path

import pytest

from agent_financial_analyst.models import (
    AgentOutput,
    ResearchReport,
    RiskFactor,
    RiskLevel,
    StockData,
)
from agent_financial_analyst.tools import (
    format_number,
    format_pct,
    stock_data_summary,
)


# ─────────────────────────────────────────────
# StockData Tests
# ─────────────────────────────────────────────

class TestStockData:
    def test_default_creation(self):
        data = StockData(ticker="AAPL")
        assert data.ticker == "AAPL"
        assert data.market_cap == 0.0
        assert data.news == []

    def test_full_creation(self):
        data = StockData(
            ticker="NVDA",
            name="NVIDIA Corporation",
            sector="Technology",
            market_cap=3.42e12,
            current_price=140.50,
            revenue_ttm=130.5e9,
            pe_ratio=45.2,
            rsi_14=62.3,
        )
        assert data.name == "NVIDIA Corporation"
        assert data.market_cap == 3.42e12
        assert data.rsi_14 == 62.3


# ─────────────────────────────────────────────
# Formatting Tests
# ─────────────────────────────────────────────

class TestFormatting:
    def test_format_trillions(self):
        assert format_number(3.42e12) == "$3.42T"

    def test_format_billions(self):
        assert format_number(130.5e9) == "$130.50B"

    def test_format_millions(self):
        assert format_number(60.9e6) == "$60.9M"

    def test_format_thousands(self):
        assert format_number(45000) == "$45.0K"

    def test_format_small(self):
        assert format_number(42.50) == "$42.50"

    def test_format_zero(self):
        assert format_number(0) == "N/A"

    def test_format_negative(self):
        assert "-" in format_number(-5e9)

    def test_format_no_prefix(self):
        result = format_number(1e9, prefix="")
        assert result == "1.00B"

    def test_format_pct_positive(self):
        assert format_pct(12.5) == "+12.5%"

    def test_format_pct_negative(self):
        assert format_pct(-5.3) == "-5.3%"

    def test_format_pct_zero(self):
        assert format_pct(0) == "N/A"


# ─────────────────────────────────────────────
# Stock Data Summary
# ─────────────────────────────────────────────

class TestStockDataSummary:
    def test_summary_contains_ticker(self):
        data = StockData(ticker="AAPL", name="Apple Inc.")
        summary = stock_data_summary(data)
        assert "AAPL" in summary
        assert "Apple Inc." in summary

    def test_summary_contains_financials(self):
        data = StockData(
            ticker="MSFT",
            name="Microsoft",
            revenue_ttm=200e9,
            pe_ratio=35.0,
            gross_margin=70.0,
        )
        summary = stock_data_summary(data)
        assert "Revenue" in summary
        assert "P/E" in summary or "35.0" in summary

    def test_summary_contains_news(self):
        data = StockData(
            ticker="GOOGL",
            news=[
                {"title": "Google announces new AI", "publisher": "Reuters"},
                {"title": "Alphabet earnings beat", "publisher": "CNBC"},
            ],
        )
        summary = stock_data_summary(data)
        assert "Google announces new AI" in summary

    def test_summary_empty_data(self):
        data = StockData(ticker="XYZ")
        summary = stock_data_summary(data)
        assert "XYZ" in summary
        # Should not crash with all zeros


# ─────────────────────────────────────────────
# Report Tests
# ─────────────────────────────────────────────

class TestResearchReport:
    def _make_report(self) -> ResearchReport:
        return ResearchReport(
            ticker="NVDA",
            date="2026-03-31",
            executive_summary="NVIDIA shows strong momentum...",
            company_overview="| Metric | Value |\n|--|--|\n| Market Cap | $3.42T |",
            fundamental_analysis="Revenue grew 114% YoY to $130.5B...",
            technical_analysis="RSI at 62.3, above 50-day MA...",
            risk_assessment="1. **Valuation Risk** (HIGH): Premium valuation...",
            conclusion="NVIDIA remains a dominant force in AI compute...",
            agent_outputs=[
                AgentOutput(agent_name="Market Data", latency_seconds=3.2),
                AgentOutput(agent_name="Fundamental", latency_seconds=5.1, tokens=2400),
                AgentOutput(agent_name="Technical", latency_seconds=2.8, tokens=1200),
                AgentOutput(agent_name="Risk", latency_seconds=3.4, tokens=1800),
                AgentOutput(agent_name="Synthesis", latency_seconds=4.7, tokens=2000),
            ],
            total_cost_usd=0.14,
            total_latency_seconds=19.2,
        )

    def test_markdown_generation(self):
        report = self._make_report()
        md = report.markdown
        assert "# NVDA — Equity Research Report" in md
        assert "Executive Summary" in md
        assert "Fundamental Analysis" in md
        assert "Technical Analysis" in md
        assert "Risk Assessment" in md
        assert "Conclusion" in md
        assert "Disclaimer" in md

    def test_markdown_contains_data(self):
        report = self._make_report()
        md = report.markdown
        assert "NVIDIA shows strong momentum" in md
        assert "Revenue grew 114%" in md

    def test_save_creates_file(self, tmp_path):
        report = self._make_report()
        filepath = report.save(str(tmp_path))
        assert filepath.exists()
        assert filepath.name == "NVDA_report.md"
        content = filepath.read_text()
        assert "NVDA" in content

    def test_save_creates_directory(self, tmp_path):
        report = self._make_report()
        nested = tmp_path / "nested" / "dir"
        filepath = report.save(str(nested))
        assert filepath.exists()

    def test_to_dict_serializable(self):
        report = self._make_report()
        d = report.to_dict()
        json.dumps(d)  # Must not raise
        assert d["ticker"] == "NVDA"
        assert d["meta"]["total_cost_usd"] == 0.14
        assert len(d["meta"]["agents"]) == 5

    def test_to_dict_structure(self):
        report = self._make_report()
        d = report.to_dict()
        assert "sections" in d
        assert "executive_summary" in d["sections"]
        assert "fundamental_analysis" in d["sections"]

    def test_empty_sections_skipped_in_markdown(self):
        report = ResearchReport(
            ticker="TEST",
            date="2026-01-01",
            executive_summary="Summary here",
        )
        md = report.markdown
        assert "Fundamental Analysis" not in md
        assert "Technical Analysis" not in md


# ─────────────────────────────────────────────
# Agent Output Tests
# ─────────────────────────────────────────────

class TestAgentOutput:
    def test_successful_output(self):
        output = AgentOutput(
            agent_name="Fundamental",
            content="Revenue analysis...",
            latency_seconds=5.1,
            tokens=2400,
        )
        assert output.error is None
        assert output.tokens == 2400

    def test_failed_output(self):
        output = AgentOutput(
            agent_name="Technical",
            error="API rate limit exceeded",
        )
        assert output.error is not None
        assert output.content == ""


# ─────────────────────────────────────────────
# Risk Factor Tests
# ─────────────────────────────────────────────

class TestRiskFactor:
    def test_risk_creation(self):
        risk = RiskFactor(
            category="Valuation",
            level=RiskLevel.HIGH,
            description="Premium valuation leaves limited margin of safety",
        )
        assert risk.level == RiskLevel.HIGH
        assert "Premium" in risk.description

    def test_risk_levels(self):
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.LOW.value == "LOW"


# ─────────────────────────────────────────────
# SEC Retriever Tests
# ─────────────────────────────────────────────

class TestSECRetriever:
    @pytest.mark.asyncio
    async def test_sec_cik_lookup(self):
        from agent_financial_analyst.tools.sec_retrieval import SECRetriever
        cik = await SECRetriever._get_cik("AAPL")
        assert cik == "0000320193"

    @pytest.mark.asyncio
    async def test_sec_get_latest_filings(self):
        from agent_financial_analyst.tools.sec_retrieval import SECRetriever
        retriever = SECRetriever()
        filings = await retriever.get_latest_filings("AAPL", count=1)
        assert len(filings) == 1
        assert filings[0]["type"] in ("10-K", "10-Q")
        assert "sec.gov" in filings[0]["url"]


# ─────────────────────────────────────────────
# API Async Background Job Tests
# ─────────────────────────────────────────────

class TestAPIAsyncJob:
    def test_health_check(self):
        # Health check is public
        from fastapi.testclient import TestClient
        from agent_financial_analyst.api.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_unauthorized_missing_key(self):
        from fastapi.testclient import TestClient
        from agent_financial_analyst.api.main import app
        client = TestClient(app)
        
        # /analyze should fail with 401
        response = client.post("/analyze", json={"ticker": "AAPL"})
        assert response.status_code == 401
        
        # /jobs should fail with 401
        response = client.get("/jobs/some-id")
        assert response.status_code == 401

    def test_unauthorized_invalid_key(self):
        from fastapi.testclient import TestClient
        from agent_financial_analyst.api.main import app
        client = TestClient(app)
        headers = {"X-API-Key": "wrong-key"}
        
        # /analyze should fail with 401
        response = client.post("/analyze", json={"ticker": "AAPL"}, headers=headers)
        assert response.status_code == 401
        assert "Invalid API Key" in response.json()["detail"]
        
        # /jobs should fail with 401
        response = client.get("/jobs/some-id", headers=headers)
        assert response.status_code == 401

    def test_authorized_job_submission_and_not_found(self):
        from fastapi.testclient import TestClient
        from agent_financial_analyst.api.main import app
        client = TestClient(app)
        headers = {"X-API-Key": "analyst_pro_dev_key_2026"}
        
        # Test 404 with valid API Key
        response = client.get("/jobs/non-existent-uuid", headers=headers)
        assert response.status_code == 404
        
        # Test 202 job submission with valid API Key
        response = client.post("/analyze", json={"ticker": "AAPL"}, headers=headers)
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["ticker"] == "AAPL"
        assert len(data["logs"]) > 0


