"""Market Data Agent implementation."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict

import yfinance as yf
from opentelemetry import trace

from ..core.base import BaseAgent
from ..schema.models import (
    Article,
    FinancialGrowth,
    MarketDataState,
    PriceAction,
    StockMetadata,
    ValuationMetrics,
)
from ..utils.logging import get_logger

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


class MarketDataAgent(BaseAgent):
    """
    Agent responsible for data ingestion and normalization.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__(agent_id="market_data_agent", model=model)

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """This agent is more of a data processor than a creative analyzer."""
        return (
            "You are a market data ingestion specialist. You ingest raw yfinance data "
            "and format it into a clean, structured JSON format for downstream analysts. "
            "Focus on precision and accuracy. If data is missing, note it clearly."
        )

    @tracer.start_as_current_span("fetch_market_data")
    async def fetch(self, ticker: str) -> MarketDataState:
        """Fetch and structure market data for a ticker."""
        logger.info(f"[MarketData] Fetching holistic data for: {ticker}")
        
        self.log_thought(
            step="initialization", 
            reasoning=f"Initializing yfinance ticker for {ticker}"
        )
        
        stock = yf.Ticker(ticker)
        
        # Parallel fetch for speed
        info_task = asyncio.to_thread(lambda: stock.info)
        history_task = asyncio.to_thread(lambda: stock.history(period="1mo"))
        news_task = asyncio.to_thread(lambda: stock.news)

        info, history, news = await asyncio.gather(info_task, history_task, news_task)
        
        self.log_thought(step="data_fetched", reasoning="Received data from yfinance APIs")

        # 1. Metadata
        metadata = StockMetadata(
            ticker=ticker.upper(),
            name=info.get("longName", info.get("shortName", ticker)),
            sector=info.get("sector", "N/A"),
            industry=info.get("industry", "N/A"),
            market_cap=info.get("marketCap", 0.0),
            employees=info.get("fullTimeEmployees"),
            description=info.get("longBusinessSummary", ""),
        )

        # 2. Valuation
        valuation = ValuationMetrics(
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            ps_ratio=info.get("priceToSalesTrailing12Months"),
            pb_ratio=info.get("priceToBook"),
            ev_ebitda=info.get("enterpriseToEbitda"),
            dividend_yield=info.get("dividendYield"),
        )

        # 3. Growth
        growth = FinancialGrowth(
            revenue_ttm=info.get("totalRevenue", 0.0),
            revenue_growth_yoy=info.get("revenueGrowth", 0.0) * 100,
            gross_margin=info.get("grossMargins", 0.0) * 100,
            operating_margin=info.get("operatingMargins", 0.0) * 100,
            net_margin=info.get("profitMargins", 0.0) * 100,
            free_cash_flow=info.get("freeCashflow", 0.0),
            debt_to_equity=info.get("debtToEquity", 0.0),
            roe=info.get("returnOnEquity", 0.0) * 100,
        )

        # 4. Price Action
        curr_price = info.get("currentPrice", 0.0)
        
        # RSI 14 calculation
        rsi = None
        if len(history) >= 14:
            deltas = history["Close"].diff().dropna()
            gains = deltas.clip(lower=0)
            losses = -deltas.clip(upper=0)
            avg_gain = gains.rolling(14).mean().iloc[-1]
            avg_loss = losses.rolling(14).mean().iloc[-1]
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

        price_action = PriceAction(
            current_price=curr_price,
            fifty_two_week_high=info.get("fiftyTwoWeekHigh", 0.0),
            fifty_two_week_low=info.get("fiftyTwoWeekLow", 0.0),
            avg_volume=info.get("averageVolume", 0),
            beta=info.get("beta", 1.0),
            sma_50=info.get("fiftyDayAverage"),
            sma_200=info.get("twoHundredDayAverage"),
            rsi_14=rsi,
        )

        # 5. News
        articles = [
            Article(
                title=n.get("title", ""),
                link=n.get("link", ""),
                published_at=datetime.fromtimestamp(n.get("providerPublishTime", 0)),
                publisher=n.get("publisher", ""),
            )
            for n in news[:10]
            if n.get("title")
        ]

        state = MarketDataState(
            metadata=metadata,
            valuation=valuation,
            growth=growth,
            price=price_action,
            news=articles,
        )
        
        logger.info(f"[MarketData] Data pipeline complete for {ticker}")
        return state
