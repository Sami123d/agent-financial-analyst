"""Research Reviewer Specialist Agent."""

from __future__ import annotations

from typing import Any, Dict

from ..core.base import BaseAgent


class ReviewerAgent(BaseAgent):
    """
    Agent responsible for critiquing and improving a draft research report.
    """

    def __init__(self, model: str = "gpt-4o"):
        super().__init__(agent_id="research_reviewer", model=model)

    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        return (
            "You are a managing director at an investment bank. Your task is to "
            "review and critique a draft research report produced by several "
            "junior analysts. Your goal is to identify and address any bias, "
            "missing data, inconsistent statements, or unsupported thesa. "
            "Your feedback should be professional, critical, and objective. "
            "Your goal is to produce a balanced and comprehensive assessment "
            "for the final synthesis."
        )

    async def review(self, report_draft: str) -> str:
        """Review the research report draft and provide critique/feedback."""
        user_prompt = (
            f"Critique this research report draft and provide feedback for the final "
            f"synthesis. Be critical, and identify any bias or missing data:\n\n"
            f"{report_draft}\n\n"
            "Format your feedback as follows:\n"
            "1. AREAS OF STRENGTH\n"
            "2. AREAS OF WEAKNESS/BIAS\n"
            "3. RECOMMENDATIONS FOR FINAL SYNTHESIS"
        )
        
        output = await self.run(user_prompt)
        return output.content
