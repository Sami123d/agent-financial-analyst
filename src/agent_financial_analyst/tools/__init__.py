"""Market data tools — fetch stock data from yfinance."""

from __future__ import annotations

import logging
from typing import Optional

from ..models import StockData

logger = logging.getLogger("agent-analyst")


def fetch_stock_data(ticker: str, max_news: int = 10) -> StockData:
    """Fetch comprehensive stock data using yfinance."""
    try:
        import yfinance as yf
    except ImportError:
        raise RuntimeError("yfinance required. Run: pip install yfinance")

    stock = yf.Ticker(ticker)
    info = stock.info or {}

    data = StockData(
        ticker=ticker.upper(),
        name=info.get("longName", info.get("shortName", ticker)),
        sector=info.get("sector", ""),
        industry=info.get("industry", ""),
        market_cap=info.get("marketCap", 0),
        employees=info.get("fullTimeEmployees", 0),
        description=info.get("longBusinessSummary", "")[:500],

        # Price
        current_price=info.get("currentPrice", info.get("regularMarketPrice", 0)),
        price_change_pct=info.get("52WeekChange", 0) * 100 if info.get("52WeekChange") else 0,
        fifty_two_week_high=info.get("fiftyTwoWeekHigh", 0),
        fifty_two_week_low=info.get("fiftyTwoWeekLow", 0),
        avg_volume=info.get("averageVolume", 0),
        beta=info.get("beta", 0),

        # Fundamentals
        revenue_ttm=info.get("totalRevenue", 0),
        revenue_growth=info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else 0,
        gross_margin=info.get("grossMargins", 0) * 100 if info.get("grossMargins") else 0,
        operating_margin=info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else 0,
        net_margin=info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0,
        eps=info.get("trailingEps", 0),
        pe_ratio=info.get("trailingPE", 0),
        forward_pe=info.get("forwardPE", 0),
        ps_ratio=info.get("priceToSalesTrailing12Months", 0),
        pb_ratio=info.get("priceToBook", 0),
        ev_ebitda=info.get("enterpriseToEbitda", 0),
        free_cash_flow=info.get("freeCashflow", 0),
        debt_to_equity=info.get("debtToEquity", 0),
        roe=info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0,
        dividend_yield=info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,

        # Technical
        sma_50=info.get("fiftyDayAverage", 0),
        sma_200=info.get("twoHundredDayAverage", 0),
    )

    # Compute technical indicators
    price = data.current_price
    if price and data.sma_50:
        data.above_50ma = price > data.sma_50
    if price and data.sma_200:
        data.above_200ma = price > data.sma_200

    # RSI calculation from price history
    try:
        hist = stock.history(period="1mo")
        if len(hist) >= 14:
            deltas = hist["Close"].diff().dropna()
            gains = deltas.clip(lower=0)
            losses = (-deltas.clip(upper=0))
            avg_gain = gains.rolling(14).mean().iloc[-1]
            avg_loss = losses.rolling(14).mean().iloc[-1]
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                data.rsi_14 = round(100 - (100 / (1 + rs)), 1)

            data.price_history = [
                {"date": str(d.date()), "close": round(float(c), 2)}
                for d, c in zip(hist.index, hist["Close"])
            ][-30:]  # Last 30 days
    except Exception as e:
        logger.debug(f"Price history error: {e}")

    # News
    try:
        news_items = stock.news or []
        data.news = [
            {
                "title": n.get("title", ""),
                "publisher": n.get("publisher", ""),
                "link": n.get("link", ""),
            }
            for n in news_items[:max_news]
            if n.get("title")
        ]
    except Exception as e:
        logger.debug(f"News error: {e}")

    return data


def format_number(n: float, prefix: str = "$") -> str:
    """Format large numbers: $1.2T, $45.3B, $120.5M."""
    if n == 0:
        return "N/A"
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    if abs_n >= 1e12:
        return f"{sign}{prefix}{abs_n/1e12:.2f}T"
    if abs_n >= 1e9:
        return f"{sign}{prefix}{abs_n/1e9:.2f}B"
    if abs_n >= 1e6:
        return f"{sign}{prefix}{abs_n/1e6:.1f}M"
    if abs_n >= 1e3:
        return f"{sign}{prefix}{abs_n/1e3:.1f}K"
    return f"{sign}{prefix}{abs_n:.2f}"


def format_pct(n: float) -> str:
    """Format percentage."""
    if n == 0:
        return "N/A"
    return f"{n:+.1f}%"


def stock_data_summary(data: StockData) -> str:
    """Create a structured text summary of stock data for agents."""
    lines = [
        f"TICKER: {data.ticker}",
        f"COMPANY: {data.name}",
        f"SECTOR: {data.sector} | INDUSTRY: {data.industry}",
        f"MARKET CAP: {format_number(data.market_cap)}",
        f"EMPLOYEES: {data.employees:,}" if data.employees else "",
        "",
        "=== PRICE ===",
        f"Current: ${data.current_price:.2f}" if data.current_price else "",
        f"52W High: ${data.fifty_two_week_high:.2f}" if data.fifty_two_week_high else "",
        f"52W Low: ${data.fifty_two_week_low:.2f}" if data.fifty_two_week_low else "",
        f"Beta: {data.beta:.2f}" if data.beta else "",
        "",
        "=== FUNDAMENTALS ===",
        f"Revenue (TTM): {format_number(data.revenue_ttm)}",
        f"Revenue Growth: {format_pct(data.revenue_growth)}",
        f"Gross Margin: {data.gross_margin:.1f}%" if data.gross_margin else "",
        f"Operating Margin: {data.operating_margin:.1f}%" if data.operating_margin else "",
        f"Net Margin: {data.net_margin:.1f}%" if data.net_margin else "",
        f"EPS: ${data.eps:.2f}" if data.eps else "",
        f"P/E: {data.pe_ratio:.1f}x" if data.pe_ratio else "",
        f"Forward P/E: {data.forward_pe:.1f}x" if data.forward_pe else "",
        f"P/S: {data.ps_ratio:.1f}x" if data.ps_ratio else "",
        f"EV/EBITDA: {data.ev_ebitda:.1f}x" if data.ev_ebitda else "",
        f"FCF: {format_number(data.free_cash_flow)}",
        f"D/E: {data.debt_to_equity:.1f}" if data.debt_to_equity else "",
        f"ROE: {data.roe:.1f}%" if data.roe else "",
        f"Dividend Yield: {data.dividend_yield:.2f}%" if data.dividend_yield else "",
        "",
        "=== TECHNICAL ===",
        f"50-day MA: ${data.sma_50:.2f} ({'above' if data.above_50ma else 'below'})" if data.sma_50 else "",
        f"200-day MA: ${data.sma_200:.2f} ({'above' if data.above_200ma else 'below'})" if data.sma_200 else "",
        f"RSI (14): {data.rsi_14}" if data.rsi_14 else "",
        "",
        "=== NEWS ===",
    ]
    for n in data.news[:5]:
        lines.append(f"- {n['title']} ({n.get('publisher', '')})")

    return "\n".join(line for line in lines if line is not None)
