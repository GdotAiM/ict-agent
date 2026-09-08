"""
Observability layer — Langfuse tracing overlay for the ICT agent.

Wraps every LLM call and tool dispatch in a Langfuse span so runs appear
in the Langfuse dashboard as traces with child observations for each stage,
tool call, and generation (with token counts and cost).

Usage (for developers):
    from harness.observability import trace_stage, trace_tool, trace_llm_call

    # Around a full stage run:
    with trace_stage("htf_bias", symbol=symbol) as span:
        result = adapter.call(...)
        span.update(confluence_score=3, gate_passed=True)

    # Around a single tool call:
    with trace_tool("get_candles", symbol=symbol, timeframe="1h"):
        df = get_candles(symbol, "1h", "10d")

    # Around an LLM call (auto-captures tokens + cost):
    response = trace_llm_call(adapter, system, tools, messages, model)
"""
from __future__ import annotations
import contextlib
import json
import os
import time
import config
from typing import Any, Generator


# ---------------------------------------------------------------------------
# Lazy Langfuse client (init only when first used, not at import time)
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
    if not public_key or not secret_key:
        _client = _NullClient()  # no-op when not configured
        return _client
    try:
        from langfuse import Langfuse
        _client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    except Exception as e:
        print(f"[OBS] Langfuse init failed: {e}")
        _client = _NullClient()
    return _client


class _NullClient:
    """No-op client used when Langfuse credentials are absent."""
    def start_as_current_observation(self, **kwargs):
        return _NullSpan()
    def flush(self):
        pass
    def shutdown(self):
        pass


class _NullSpan:
    """No-op span that silently ignores all calls."""
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def update(self, **kw): pass
    def capture_exception(self, *a, **kw): pass


# ---------------------------------------------------------------------------
# Cost map (per-token prices in USD)
# ---------------------------------------------------------------------------

MODEL_PRICING = {
    # Key matches the 'model' string in adapter.name (e.g. "agnes-2.5-flash")
    # Fallback pricing if model not found
    "default": {"input": 0.5e-6, "output": 2.0e-6},
}
# Add more models here as needed:
# "claude-sonnet-4-20250514": {"input": 3.0e-6, "output": 15.0e-6},


def _compute_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    return round(input_tokens * pricing["input"] + output_tokens * pricing["output"], 6)


# ---------------------------------------------------------------------------
# Decorator / context manager for LLM calls
# ---------------------------------------------------------------------------

def trace_llm_call(
    adapter,
    system_prompt: str,
    tools: list,
    messages: list,
    model_name: str | None = None,
    extra_tags: dict | None = None,
) -> dict:
    """
    Call the adapter and wrap the result in a Langfuse generation span.
    Returns the raw adapter response (unchanged shape).
    """
    client = _get_client()
    model = model_name or adapter.name
    tags = {**extra_tags} if extra_tags else {}

    with client.start_as_current_observation(
        name=f"llm:{model}",
        as_type="generation",
        model=model,
        input={"messages": messages, "system": system_prompt[:500]},
        metadata={"adapter": adapter.name, **tags},
    ) as span:
        start = time.time()
        response = adapter.call(system_prompt, tools, messages)
        elapsed_ms = int((time.time() - start) * 1000)

        usage = response.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        cost = _compute_cost(input_tokens, output_tokens, model)

        span.update(
            model=model,
            model_parameters={"temperature": config.LLM_TEMPERATURE, "top_p": config.LLM_TOP_P},
            usage_details={"input": input_tokens, "output": output_tokens},
            cost_details={"input": input_tokens, "output": output_tokens, "total_usd": cost},
            metadata={**tags, "elapsed_ms": elapsed_ms, "model": model},
        )
        return response


# ---------------------------------------------------------------------------
# Context managers for stages and tools
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def trace_stage(stage_name: str, symbol: str, **extra_attrs) -> Generator[ Any, None, None ]:
    """
    Yield a span representing one chained-loop stage.
    Call .update(gate_passed=True, confluence_score=3) on the span before exiting.
    """
    client = _get_client()
    with client.start_as_current_observation(
        name=f"stage:{stage_name}",
        as_type="span",
        input={"symbol": symbol, **extra_attrs},
        metadata={"stage": stage_name, "symbol": symbol},
    ) as span:
        try:
            yield span
        except Exception as e:
            span.capture_exception(e)
            raise


@contextlib.contextmanager
def trace_tool(tool_name: str, symbol: str, **extra_input) -> Generator[ Any, None, None ]:
    """Yield a span around a single tool dispatch."""
    client = _get_client()
    with client.start_as_current_observation(
        name=f"tool:{tool_name}",
        as_type="span",
        input={"symbol": symbol, **extra_input},
        metadata={"tool": tool_name, "symbol": symbol},
    ) as span:
        try:
            yield span
        except Exception as e:
            span.capture_exception(e)
            raise


def finalize_trace(trace_id: str, symbol: str, decision: str, confluence: int,
                   total_tokens_in: int, total_tokens_out: int) -> None:
    """Add final attributes/scores to the active trace before it closes."""
    client = _get_client()
    try:
        client.score_current_trace(
            name="decision",
            value=1 if decision == "trade" else 0,
            comment=decision,
            metadata={"symbol": symbol, "confluence": confluence,
                      "tokens_in": total_tokens_in, "tokens_out": total_tokens_out},
        )
    except Exception:
        pass  # non-critical — don't break the run


@contextlib.contextmanager
def trace_chain(symbol: str, mode: str = "chained") -> Generator[ Any, None, None ]:
    """
    Root-level trace for an entire analysis cycle.
    All stages and tool calls within will be child spans of this trace.
    Usage:
        with trace_chain("XAUUSD", mode="chained") as root:
            result = run_chained(...)
    """
    client = _get_client()
    with client.start_as_current_observation(
        name=f"chain:{mode}",
        as_type="span",
        input={"symbol": symbol, "mode": mode},
        metadata={"symbol": symbol, "mode": mode,
                  "budget_per_stage": config.TOKEN_BUDGET_PER_STAGE,
                  "budget_per_cycle": config.TOKEN_BUDGET_PER_CYCLE,
                  "temperature": config.LLM_TEMPERATURE,
                  "top_p": config.LLM_TOP_P},
    ) as span:
        try:
            yield span
        except Exception as e:
            span.capture_exception(e)
            raise
