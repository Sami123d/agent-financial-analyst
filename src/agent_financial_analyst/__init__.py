"""agent-financial-analyst: Multi-agent equity research, automated."""

from .models import ResearchReport, StockData, AgentOutput
from .agents import FinancialAnalyst

__version__ = "0.1.0"
__all__ = ["AgentOutput", "FinancialAnalyst", "ResearchReport", "StockData"]
