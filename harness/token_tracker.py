"""
TokenTracker — counts tokens reported by LLM adapters and enforces budgets.

Usage (in harness/chained_loop.py):
    tracker = TokenTracker()
    ...
    response = adapter.call(...)
    tracker.add(response)          # returns True if within budget
    tracker.check_stage()          # raises BudgetExceeded when per-stage limit hit
    tracker.check_cycle()          # raises BudgetExceeded when per-cycle limit hit
"""
from __future__ import annotations
import config


class BudgetExceeded(Exception):
    """Raised when a token budget is exceeded."""


class TokenTracker:
    def __init__(self) -> None:
        self._stage_tokens = 0
        self._cycle_tokens = 0

    # ---- mutating -------------------------------------------------------
    def add(self, response) -> bool:
        """Accumulate tokens from one LLM response. Returns False when any
        budget is exceeded (exception also raised for immediate handling)."""
        usage = None
        # 1) Raw response object with .usage (e.g. Anthropic native)
        if hasattr(response, "usage"):
            usage = response.usage
        # 2) Dict-wrapped response (OpenAI-compatible adapters)
        elif isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
        if usage is None:
            return True  # can't count → trust the model

        if isinstance(usage, dict):
            prompt = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
            completion = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        else:
            prompt = int(getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", 0)))
            completion = int(getattr(usage, "output_tokens", getattr(usage, "completion_tokens", 0)))

        total = prompt + completion
        self._stage_tokens += total
        self._cycle_tokens += total

        if self._stage_tokens > config.TOKEN_BUDGET_PER_STAGE:
            raise BudgetExceeded(
                f"Stage token budget exceeded ({self._stage_tokens} > {config.TOKEN_BUDGET_PER_STAGE})"
            )
        if self._cycle_tokens > config.TOKEN_BUDGET_PER_CYCLE:
            raise BudgetExceeded(
                f"Cycle token budget exceeded ({self._cycle_tokens} > {config.TOKEN_BUDGET_PER_CYCLE})"
            )
        return True

    def stage_used(self) -> int:
        return self._stage_tokens

    def cycle_used(self) -> int:
        return self._cycle_tokens

    def check_cycle(self) -> None:
        """Raise BudgetExceeded if the cycle total has crossed the limit."""
        if self._cycle_tokens > config.TOKEN_BUDGET_PER_CYCLE:
            raise BudgetExceeded(
                f"Cycle token budget exceeded ({self._cycle_tokens} > {config.TOKEN_BUDGET_PER_CYCLE})"
            )

    def reset_stage(self) -> None:
        self._stage_tokens = 0
