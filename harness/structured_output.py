"""
Structured Output — Pydantic schemas for each analysis stage.

Instead of relying on fragile regex over free-form prose, each stage
now declares a Pydantic model. The prompt requests JSON; the gate
parser tries JSON first (stripping markdown fences if present), then
falls back to regex for older sessions / partial outputs.

This makes downstream consumption deterministic: callers read
gate_result.extracted directly without re-parsing strings.
"""
from __future__ import annotations
import json
import re
from typing import Literal

try:
    from pydantic import BaseModel, Field, validator
except ImportError:  # pragma: no cover — pydantic is a hard dep
    BaseModel = object  # type: ignore

# ---------------------------------------------------------------------------
# Stage schemas
# ---------------------------------------------------------------------------


class HTFBiasOutput(BaseModel):
    """Stage 1 — Higher Timeframe Bias."""
    bias: Literal["BULLISH", "BEARISH", "RANGING"]
    draw_on_liquidity: str = Field(
        description="BSL or SSL target with price level, e.g. 'SSL at 4617.28'"
    )
    pd_array: Literal["PREMIUM", "DISCOUNT", "EQUILIBRIUM"]


class TimingOutput(BaseModel):
    """Stage 2 — Timing & Kill Zone context."""
    kill_zone: Literal["LONDON", "NY_AM", "NY_PM", "ASIAN", "OUTSIDE"]
    in_kill_zone: bool = Field(
        default=False, description="Whether we are inside a high-probability window"
    )
    exceptional_justification: str | None = Field(
        default=None, description="Why proceeding outside kill zones, if applicable"
    )


class LTFEntryOutput(BaseModel):
    """Stage 3 — Entry model on lower timeframe."""
    entry_trigger: str = Field(
        description="FVG or Order Block + timeframe, or 'NONE' if absent"
    )
    invalidation: str = Field(
        description="Stop level — price or structure level"
    )
    target: str = Field(
        description="Draw-on-liquidity target price or level"
    )
    rr_ratio: float | None = Field(
        default=None, description="Calculated reward:risk ratio, if computed"
    )


class RiskExecOutput(BaseModel):
    """Stage 4 — Confluence scoring and final decision."""
    confluence_score: int = Field(
        ge=0, le=4, description="0-4 based on structure+liquidity+PD+trigger"
    )
    decision: Literal["TRADE", "WATCH", "NO_SETUP"]


# ---------------------------------------------------------------------------
# JSON parser — strips markdown fences, parses, validates
# ---------------------------------------------------------------------------

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def extract_json(text: str) -> dict | None:
    """Try to pull a JSON object out of model output.

    Handles:
      - Bare JSON: '{"bias": ...}'
      - Fenced JSON: ```json\n{...}\n```
      - Mixed prose with JSON at end
    Returns parsed dict or None if no valid JSON found.
    """
    # Try fenced first
    m = _JSON_FENCE.search(text)
    if m:
        candidate = m.group(1)
    else:
        # Find first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start : end + 1]

    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Validate stage output against Pydantic schema
# ---------------------------------------------------------------------------

_SCHEMA_MAP = {
    "htf_bias": HTFBiasOutput,
    "timing": TimingOutput,
    "ltf_entry": LTFEntryOutput,
    "risk_exec": RiskExecOutput,
}


def parse_structured_output(stage: str, text: str) -> dict | None:
    """Parse structured output for a stage.

    Tries JSON-first (with fence stripping), falls back to the legacy
    regex parser in gates.py. Returns a flat dict of extracted fields
    ready for gate validation.
    """
    schema_cls = _SCHEMA_MAP.get(stage)
    if schema_cls is None:
        return None

    # --- Try JSON path ---
    raw = extract_json(text)
    if raw is not None:
        try:
            instance = schema_cls(**raw)
            return instance.model_dump()
        except Exception:
            pass  # fall through to regex

    # --- Fallback: regex (legacy behavior) ---
    from agent.gates import parse_structured

    structured = parse_structured(text)
    if not structured:
        return None

    # Map regex-extracted keys to schema fields
    result: dict = {}
    if stage == "htf_bias":
        bias_val = structured.get("bias", "").upper()
        if bias_val in ("BULLISH", "BEARISH", "RANGING"):
            result["bias"] = bias_val
        if structured.get("draw_on_liquidity"):
            result["draw_on_liquidity"] = structured["draw_on_liquidity"]
        pd = structured.get("pd_array", "").upper()
        if pd in ("PREMIUM", "DISCOUNT", "EQUILIBRIUM"):
            result["pd_array"] = pd
    elif stage == "timing":
        kz = structured.get("kill_zone", "").upper()
        if kz in ("LONDON", "NY_AM", "NY_PM", "ASIAN", "OUTSIDE"):
            result["kill_zone"] = kz
        result["in_kill_zone"] = kz not in ("OUTSIDE", "ASIAN")
    elif stage == "ltf_entry":
        if structured.get("entry_trigger"):
            result["entry_trigger"] = structured["entry_trigger"]
        if structured.get("invalidation"):
            result["invalidation"] = structured["invalidation"]
        if structured.get("target"):
            result["target"] = structured["target"]
    elif stage == "risk_exec":
        score_str = structured.get("confluence_score", "")
        if score_str.isdigit():
            result["confluence_score"] = int(score_str)
        dec = structured.get("decision", "").upper()
        if dec in ("TRADE", "WATCH", "NO_SETUP"):
            result["decision"] = dec

    return result if result else None


# ---------------------------------------------------------------------------
# Structured hints — updated to request JSON
# ---------------------------------------------------------------------------

STAGE_JSON_HINTS = {
    "htf_bias": """
At the end of your narrative, output ONLY this JSON object (no markdown fences):
{"bias": "BEARISH", "draw_on_liquidity": "SSL at 4617.28", "pd_array": "PREMIUM"}
Valid bias values: BULLISH, BEARISH, RANGING.
Valid pd_array values: PREMIUM, DISCOUNT, EQUILIBRIUM.
""",
    "timing": """
At the end of your narrative, output ONLY this JSON object (no markdown fences):
{"kill_zone": "NY_AM", "in_kill_zone": true}
Valid kill_zone values: LONDON, NY_AM, NY_PM, ASIAN, OUTSIDE.
""",
    "ltf_entry": """
At the end of your narrative, output ONLY this JSON object (no markdown fences):
{"entry_trigger": "NONE", "invalidation": "N/A", "target": "N/A"}
If no trigger exists set entry_trigger to "NONE". Provide explicit stop/target when available.
""",
    "risk_exec": """
At the end of your narrative, output ONLY this JSON object (no markdown fences):
{"confluence_score": 3, "decision": "NO_SETUP"}
confluence_score must be 0-4. decision must be TRADE, WATCH, or NO_SETUP.
""",
}
