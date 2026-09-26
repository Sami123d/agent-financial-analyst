"""Base infrastructure for the multi-agent system."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import backoff
import httpx
from openai import AsyncOpenAI
from opentelemetry import trace

from ..schema.models import AgentOutput, AgentThought
from ..utils.logging import get_logger

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)

# Price per 1M tokens (March 2026 update)
PRICING = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "claude-3-opus": (15.00, 75.00),
    "claude-3-sonnet": (3.00, 15.00),
}


class BaseAgent(ABC):
    """
    Standard agent interface with telemetry, cost tracking, and 
    robust error handling.
    """

    def __init__(self, agent_id: str, model: str = "gpt-4o-mini"):
        self.agent_id = agent_id
        self.model = model
        self.client = AsyncOpenAI()
        self.thoughts: List[AgentThought] = []
        self.last_output: AgentOutput | None = None

    @abstractmethod
    def get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Override to define your agent's persona and instructions."""
        pass

    @backoff.on_exception(backoff.expo, (httpx.HTTPError, Exception), max_tries=3)
    @tracer.start_as_current_span("agent_run")
    async def run(self, user_prompt: str, context: Dict[str, Any] = None) -> AgentOutput:
        """Execute the agent loop."""
        context = context or {}
        system_prompt = self.get_system_prompt(context)
        
        start_time = time.perf_counter()
        
        logger.info(f"[{self.agent_id}] Starting task with model: {self.model}")
        
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
            )
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            prompt_tokens = resp.usage.prompt_tokens
            completion_tokens = resp.usage.completion_tokens
            cost = self._calculate_cost(self.model, prompt_tokens, completion_tokens)
            
            output = AgentOutput(
                agent_id=self.agent_id,
                content=resp.choices[0].message.content,
                latency_ms=latency_ms,
                tokens_prompt=prompt_tokens,
                tokens_completion=completion_tokens,
                cost_usd=cost,
                thoughts=self.thoughts,
            )
            self.last_output = output
            
            logger.info(f"[{self.agent_id}] Completed in {latency_ms/1000:.2f}s | Cost: ${cost:.4f}")
            
            return output
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Execution failed: {str(e)}")
            raise

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate the USD cost of the LLM call."""
        rates = PRICING.get(model, PRICING["gpt-4o"])
        input_cost = (prompt_tokens / 1_000_000) * rates[0]
        output_cost = (completion_tokens / 1_000_000) * rates[1]
        return input_cost + output_cost

    def log_thought(self, step: str, reasoning: str, tool: str = None, observation: str = None):
        """Record an internal thought step."""
        thought = AgentThought(
            step=step, reasoning=reasoning, tool_used=tool, observation=observation
        )
        self.thoughts.append(thought)
        logger.debug(f"[{self.agent_id}] TRACE: {step} - {reasoning}")
