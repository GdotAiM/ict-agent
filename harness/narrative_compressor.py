"""
NarrativeCompressor — summarizes accumulated stage narratives into a compact
brief for passing between stages.

Instead of pasting the full Stage 1 narrative (~1500-3000 tokens) into
Stages 2-4, we compress it to ~200 tokens using a lightweight LLM call.
This keeps token budgets stable while preserving the essential context.
"""
from __future__ import annotations
import config


COMPRESSION_PROMPT = """You are a trading analyst summarizing previous analysis stages.
Extract only the concrete factual findings — numbers, levels, biases, zones.
Omit all prose, reasoning, and ICT doctrine references.
Output format (exact fields, one per line):

BIAS: <BULLISH|BEARISH|RANGING>
PRICE: <current price or ?>
ZONE: <PREMIUM|DISCOUNT|EQUILIBRIUM>
BSL: <buy-side liquidity level(s) or ?>
SSL: <sell-side liquidity level(s) or ?>
KILL_ZONE: <LONDON|NY_AM|NY_PM|ASIAN|OUTSIDE>
ENTRY_STATUS: <PENDING|NONE|<description>>
NOTE: <one-line contextual note, max 40 chars>

If a field has no value, write "?"."""


def _compress_with_llm(accumulator: list[str], adapter, system_prompt: str,
                       messages: list) -> str:
    """One-shot LLM compression. Returns compact brief string."""
    full_text = "\n\n".join(accumulator[-3:])  # keep last 3 stages max
    # Truncate if absurdly long (defensive)
    if len(full_text) > 8000:
        full_text = full_text[-8000:]
        full_text = "...[truncated]...\n" + full_text

    messages.append({"role": "user", "content": f"{COMPRESSION_PROMPT}\n\nPrevious analysis stages:\n{full_text}"})
    try:
        response = adapter.call(system_prompt, [], messages)
        text = response.get("text", "").strip()
        # Clean up any JSON wrapper if present
        if text.startswith("{"):
            import json
            try:
                parsed = json.loads(text)
                lines = [f"{k}: {v}" for k, v in parsed.items() if v]
                text = "\n".join(lines)
            except Exception:
                pass
        return text[:600]  # hard cap
    except Exception:
        return "[compression failed — using raw]"
    finally:
        # Remove the temporary message we added
        if messages and messages[-1].get("role") == "user" and COMPRESSION_PROMPT in messages[-1].get("content", ""):
            messages.pop()


def compress_narratives(accumulator: list[str], adapter, system_prompt: str,
                        messages: list) -> tuple[list[str], str]:
    """
    Compress accumulated stage narratives into a brief.
    Returns (updated_accumulator, brief_text).

    If there's only one stage or no adapter available, returns raw.
    """
    if len(accumulator) <= 1:
        return accumulator, accumulator[-1] if accumulator else ""

    try:
        brief = _compress_with_llm(accumulator, adapter, system_prompt, messages)
        # Keep raw for synthesis fallback but use brief for prompt context
        return accumulator, brief
    except Exception:
        # Fallback: join last two stages raw
        return accumulator, "\n---\n".join(accumulator[-2:])
