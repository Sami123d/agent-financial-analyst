"""Document Analyst Specialist Agent."""

from __future__ import annotations

from typing import Any, Dict

from ..core.base import BaseAgent
from ..tools.sec_retrieval import SECRetriever


class DocumentAnalystAgent(BaseAgent):
    """
    Agent specializing in deep reading of SEC filings and transcripts.
    """

    def __init__(self, model: str = "gpt-4o"):
        super().__init__(agent_id="document_analyst", model=model)
        self.retriever = SECRetriever()

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return (
            "You are a specialized document analyst for institutional research. "
            "Your role is to extract critical findings, risks, and forward-looking "
            "statements from SEC filings (10-K, 10-Q) and earnings call transcripts. "
            "Focus on management guidance, supply chain commentary, and competitive "
            "positioning. Be critical, and look for discrepancies between management "
            "narrative and financial reality."
        )

    async def analyze_filings(self, ticker: str) -> str:
        """Fetch and analyze the latest SEC filings."""
        self.log_thought(
            step="fetching_filings", 
            reasoning=f"Requesting latest 10-K/10-Q metadata for {ticker}"
        )
        
        filings = await self.retriever.get_latest_filings(ticker, count=2)
        
        # Take the first (latest) filing
        latest = filings[0]
        
        # Extraction (using mock text from tool for demo)
        sections = await self.retriever.get_filing_sections(
            latest["url"], ["Item 1A", "Item 7"]
        )
        
        mda_section = sections.get("Item 7. Management's Discussion and Analysis", "")
        risk_section = sections.get("Item 1A. Risk Factors", "")

        user_prompt = (
            f"Analyze the following sections from the {latest['type']} filing for {ticker} "
            f"dated {latest['date']}:\n\n"
            f"RISK FACTORS:\n{risk_section}\n\n"
            f"MD&A:\n{mda_section}\n\n"
            "Summarize the 3 most critical findings and 3 most significant risks "
            "mentioned by management. Use professional formatting."
        )
        
        output = await self.run(user_prompt)
        return output.content
