"""
Gate checks for the ICT staged prompt-chaining workflow.

These are pure Python validators — no LLM inside the gate.
They inspect the narrative text (+ optional structured block) from a stage
and decide whether the agent is allowed to proceed.

Udacity Output Validation mapping:
  - Format checks  → required structured fields (BIAS, DRAW_ON_LIQUIDITY, …)
  - Content checks → ICT keywords / phrases
  - Logic checks   → confluence score, implied R:R when numbers appear

On failure the chained loop can:
  - halt
  - retry the stage
  - retry the stage with the failure reason injected into the prompt
"""
from __future__ import annotations
import re
from harness.structured_output import parse_structured_output
from dataclasses import dataclass, field


@dataclass
class GateResult:
    passed: bool
    reason: str
    extracted: dict = field(default_factory=dict)
    soft: bool = False          # soft gates can be overridden
    feedback: str = ""          # human-readable feedback to inject on retry


# ---------------------------------------------------------------------------
# Structured-block parser
# ---------------------------------------------------------------------------

_STRUCTURED_PATTERNS = {
    "bias": re.compile(
        r"BIAS\s*:\s*(BULLISH|BEARISH|RANGING)", re.IGNORECASE
    ),
    "draw_on_liquidity": re.compile(
        r"DRAW_ON_LIQUIDITY\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE
    ),
    "pd_array": re.compile(
        r"PD_ARRAY\s*:\s*(PREMIUM|DISCOUNT|EQUILIBRIUM)", re.IGNORECASE
    ),
    "kill_zone": re.compile(
        r"KILL_ZONE\s*:\s*(LONDON|NY_AM|NY_PM|ASIAN|OUTSIDE|INSIDE.+?)(?:\n|$)",
        re.IGNORECASE,
    ),
    "entry_trigger": re.compile(
        r"ENTRY_TRIGGER\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE
    ),
    "invalidation": re.compile(
        r"INVALIDATION\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE
    ),
    "target": re.compile(
        r"TARGET\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE
    ),
    "confluence_score": re.compile(
        r"CONFLUENCE_SCORE\s*:\s*([0-4])", re.IGNORECASE
    ),
    "decision": re.compile(
        r"DECISION\s*:\s*(TRADE|WATCH|NO_SETUP)", re.IGNORECASE
    ),
}


def parse_structured(text: str) -> dict:
    """Extract key=value style lines the stages are instructed to emit."""
    out = {}
    for key, pat in _STRUCTURED_PATTERNS.items():
        m = pat.search(text)
        if m:
            out[key] = m.group(1).strip()
    return out


# ---------------------------------------------------------------------------
# Liquidity-sequencing parser (prompts/forward_test/02_draw_on_liquidity —
# the "FORWARD LIQUIDITY SEQUENCING ENGINE" prompt). Separate from
# _STRUCTURED_PATTERNS above because this format has fields whose values
# sit on the LINE AFTER the label (not "KEY: value" on one line), plus
# multi-line numbered lists and a nested conditional block that a single-
# line regex can't capture.
# ---------------------------------------------------------------------------

_SEQUENCING_PATTERNS = {
    "htf_directional_bias": re.compile(
        r"HTF_DIRECTIONAL_BIAS\s*:?\s*\n?\s*(BULLISH|BEARISH|UNCLEAR)", re.IGNORECASE
    ),
    "price_location": re.compile(
        r"PRICE_LOCATION\s*:?\s*\n?\s*(PREMIUM|EQUILIBRIUM|DISCOUNT)", re.IGNORECASE
    ),
    "first_liquidity_event": re.compile(
        r"FIRST_LIQUIDITY_EVENT\s*:?\s*\n?\s*(BSL|SSL|UNCLEAR)", re.IGNORECASE
    ),
    "first_liquidity_confidence": re.compile(
        r"FIRST_LIQUIDITY_CONFIDENCE\s*:?\s*\n?\s*(HIGH|MEDIUM|LOW)", re.IGNORECASE
    ),
    "bsl_vulnerability": re.compile(
        r"BSL_VULNERABILITY\s*:?\s*\n?\s*(HIGH|MEDIUM|LOW)", re.IGNORECASE
    ),
    "ssl_vulnerability": re.compile(
        r"SSL_VULNERABILITY\s*:?\s*\n?\s*(HIGH|MEDIUM|LOW)", re.IGNORECASE
    ),
    "expected_sequence": re.compile(
        r"EXPECTED_SEQUENCE\s*:?\s*\n?\s*"
        r"(BSL\s*(?:→|->)\s*SSL|SSL\s*(?:→|->)\s*BSL|BSL\s*(?:→|->)\s*BSL|"
        r"SSL\s*(?:→|->)\s*SSL|UNCLEAR)",
        re.IGNORECASE,
    ),
    "invalidation": re.compile(
        r"(?<![A-Z_])INVALIDATION\s*:?\s*\n?\s*(.+?)(?:\n\s*\n|\nCONFIDENCE|\nREASONING|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    # negative lookbehind excludes matching inside "FIRST_LIQUIDITY_CONFIDENCE"
    "confidence": re.compile(
        r"(?<!FIRST_LIQUIDITY_)(?<![A-Z_])CONFIDENCE\s*:?\s*\n?\s*(HIGH|MEDIUM|LOW)",
        re.IGNORECASE,
    ),
}


def _capture_block(text: str, start_key: str, end_keys: list) -> str | None:
    """Grab everything from start_key's line up to the next end_key line."""
    start_pat = re.compile(rf"{re.escape(start_key)}\s*:?\s*\n", re.IGNORECASE)
    m = start_pat.search(text)
    if not m:
        return None
    rest = text[m.end():]
    end_pos = len(rest)
    for ek in end_keys:
        em = re.search(rf"^{re.escape(ek)}\s*:?\s*$", rest, re.IGNORECASE | re.MULTILINE)
        if em:
            end_pos = min(end_pos, em.start())
    return rest[:end_pos].strip()


def _parse_numbered_list(block: str | None) -> list:
    if not block:
        return []
    items = []
    for line in block.splitlines():
        line = line.strip()
        m = re.match(r"^\d+\.\s*(.+)$", line)
        if m and m.group(1).strip():
            items.append(m.group(1).strip())
    return items


def parse_sequencing_structured(text: str) -> dict:
    """Full parse of a FORWARD LIQUIDITY SEQUENCING ENGINE response:
    single-line fields + the two numbered pool lists + whether the
    post-sweep decision tree was actually filled in (not left as a
    template with blank NEXT_DRAW = lines)."""
    out = {}
    for key, pat in _SEQUENCING_PATTERNS.items():
        m = pat.search(text)
        if m:
            out[key] = m.group(1).strip()

    out["buy_side_pools"] = _parse_numbered_list(
        _capture_block(text, "BUY_SIDE_POOLS", ["SELL_SIDE_POOLS", "NEAREST_BSL"])
    )
    out["sell_side_pools"] = _parse_numbered_list(
        _capture_block(text, "SELL_SIDE_POOLS", ["NEAREST_BSL", "NEAREST_SSL"])
    )

    tree_block = _capture_block(text, "POST-SWEEP DECISION TREE", ["SESSION_PROFILE"])
    filled_next_draws = 0
    if tree_block:
        for line in tree_block.splitlines():
            m = re.match(r"^\s*NEXT_DRAW\s*=\s*(.+)$", line)
            if m and m.group(1).strip():
                filled_next_draws += 1
    out["post_sweep_next_draws_filled"] = filled_next_draws

    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _text_contains_any(text: str, phrases: list[str]) -> bool:
    t = text.lower()
    return any(p.lower() in t for p in phrases)


def _extract_bias(text: str, structured: dict) -> str | None:
    if "bias" in structured:
        return structured["bias"].upper()
    t = text.lower()
    if re.search(r"\b(bullish|bull)\b", t) and not re.search(
        r"\b(not bullish|bearish bias)\b", t
    ):
        if "ranging" in t or "range-bound" in t or "no clear bias" in t:
            return "RANGING"
        return "BULLISH"
    if re.search(r"\b(bearish|bear)\b", t) and not re.search(
        r"\b(not bearish|bullish bias)\b", t
    ):
        if "ranging" in t or "range-bound" in t or "no clear bias" in t:
            return "RANGING"
        return "BEARISH"
    if "ranging" in t or "range-bound" in t or "no clear" in t or "unclear bias" in t:
        return "RANGING"
    return None


def _has_draw_on_liquidity(text: str, structured: dict) -> bool:
    if structured.get("draw_on_liquidity"):
        return True
    return _text_contains_any(text, [
        "draw on liquidity", "drawn to", "liquidity target",
        "bsl", "ssl", "buy-side liquidity", "sell-side liquidity",
        "equal highs", "equal lows", "old high", "old low",
        "liquidity pool", "resting liquidity",
    ])


def _has_pd_array(text: str, structured: dict) -> bool:
    if structured.get("pd_array"):
        return True
    return _text_contains_any(text, [
        "premium", "discount", "equilibrium", "pd array",
        "dealing range", "50%", "otp", "otd",
    ])


def _has_kill_zone_mention(text: str, structured: dict) -> bool:
    if structured.get("kill_zone"):
        return True
    return _text_contains_any(text, [
        "kill zone", "london", "new york", "ny am", "ny pm",
        "asian session", "in session", "outside kill zone",
        "high probability window", "low probability",
    ])


def _has_entry_trigger(text: str, structured: dict) -> bool:
    if structured.get("entry_trigger"):
        return True
    return _text_contains_any(text, [
        "fair value gap", "fvg", "order block", "ob ", "orderblock",
        "entry trigger", "mitigation", "imbalance", "breaker",
        "liquidity sweep", "sweep of",
    ])


def _has_invalidation_and_target(text: str, structured: dict) -> bool:
    has_stop = bool(structured.get("invalidation")) or _text_contains_any(text, [
        "stop", "invalidation", "beyond the", "below the low", "above the high",
        "stop loss", "sl ",
    ])
    has_target = bool(structured.get("target")) or _text_contains_any(text, [
        "target", "take profit", "tp ", "draw on", "reward", "r:r", "rr ",
    ])
    return has_stop and has_target


def _confluence_score(text: str, structured: dict) -> int:
    if structured.get("confluence_score"):
        try:
            return int(structured["confluence_score"])
        except ValueError:
            pass
    score = 0
    bias = _extract_bias(text, structured)
    if bias in ("BULLISH", "BEARISH"):
        score += 1
    if _has_draw_on_liquidity(text, structured):
        score += 1
    if _has_pd_array(text, structured):
        score += 1
    if _has_entry_trigger(text, structured):
        score += 1
    return score


def _extract_rr(text: str) -> float | None:
    """Best-effort extraction of an R:R number from free text."""
    m = re.search(r"(?:r\s*:\s*r|reward\s*:\s*risk|rr)\s*[:=]?\s*([\d.]+)", text, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    m = re.search(r"([\d.]+)\s*[xX]\s*(?:rr|r\b)", text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Stage gates
# ---------------------------------------------------------------------------

def gate_htf_bias(narrative: str, tool_results: list | None = None) -> GateResult:
    # Try JSON-first structured parsing, fall back to regex
    json_structured = parse_structured_output("htf_bias", narrative) or {}
    regex_structured = parse_structured(narrative)
    structured = {**regex_structured, **json_structured}
    bias = _extract_bias(narrative, structured)
    has_liq = _has_draw_on_liquidity(narrative, structured)
    has_pd = _has_pd_array(narrative, structured)

    extracted = {
        "bias": bias,
        "has_draw_on_liquidity": has_liq,
        "has_pd_array": has_pd,
        "structured": structured,
    }

    missing = []
    if bias is None:
        missing.append("BIAS (BULLISH / BEARISH / RANGING)")
    if not has_liq:
        missing.append("DRAW_ON_LIQUIDITY (BSL/SSL or equal highs/lows)")
    if not has_pd:
        missing.append("PD_ARRAY (PREMIUM / DISCOUNT / EQUILIBRIUM)")

    if missing:
        feedback = (
            "Your Stage-1 narrative is incomplete. You MUST end the stage with "
            "these explicit lines (exact keys):\n"
            "BIAS: BULLISH|BEARISH|RANGING\n"
            "DRAW_ON_LIQUIDITY: <description of BSL or SSL target>\n"
            "PD_ARRAY: PREMIUM|DISCOUNT|EQUILIBRIUM\n\n"
            f"Missing or unclear: {', '.join(missing)}.\n"
            "Re-analyse the HTF tools and emit the structured block."
        )
        return GateResult(
            passed=False,
            reason=f"HTF Bias gate failed — missing: {', '.join(missing)}",
            extracted=extracted,
            feedback=feedback,
        )

    return GateResult(
        passed=True,
        reason=f"HTF Bias locked: {bias}. Liquidity and PD array present.",
        extracted=extracted,
    )


def gate_timing(narrative: str, tool_results: list | None = None) -> GateResult:
    json_structured = parse_structured_output("timing", narrative) or {}
    regex_structured = parse_structured(narrative)
    structured = {**regex_structured, **json_structured}
    has_kz = _has_kill_zone_mention(narrative, structured)
    t = narrative.lower()
    inside = _text_contains_any(t, [
        "inside kill zone", "in london", "in new york", "ny am", "ny_am",
        "high probability", "in session", "kill zone is active",
    ]) or (structured.get("kill_zone", "").upper() in (
        "LONDON", "NY_AM", "NY_PM", "INSIDE"
    ))
    outside = _text_contains_any(t, [
        "outside kill zone", "low probability", "asian only", "not in kill zone",
        "outside the window",
    ]) or (structured.get("kill_zone", "").upper() in ("OUTSIDE", "ASIAN"))
    exceptional = _text_contains_any(t, [
        "exceptional", "high conviction", "strong confluence", "clear sweep",
        "proceed anyway", "override",
    ])

    extracted = {
        "mentioned_kill_zone": has_kz,
        "appears_inside": inside,
        "appears_outside": outside,
        "exceptional_justification": exceptional,
        "structured": structured,
    }

    if inside or not outside:
        return GateResult(
            passed=True,
            reason="Timing gate passed (inside or neutral kill-zone context).",
            extracted=extracted,
            soft=True,
        )
    if outside and exceptional:
        return GateResult(
            passed=True,
            reason="Timing gate passed with exceptional-setup justification outside kill zone.",
            extracted=extracted,
            soft=True,
        )

    feedback = (
        "Timing gate failed. You appear to be outside high-probability kill zones "
        "without an explicit exceptional justification.\n"
        "Either:\n"
        "  - confirm you are inside London / NY AM / NY PM, or\n"
        "  - clearly state why this setup is exceptional enough to take outside "
        "the windows (use the word 'exceptional' or 'high conviction').\n"
        "Emit: KILL_ZONE: LONDON|NY_AM|NY_PM|OUTSIDE"
    )
    return GateResult(
        passed=False,
        reason="Timing gate failed: outside kill zones without exceptional justification.",
        extracted=extracted,
        soft=True,
        feedback=feedback,
    )


def gate_ltf_entry(narrative: str, tool_results: list | None = None) -> GateResult:
    json_structured = parse_structured_output("ltf_entry", narrative) or {}
    regex_structured = parse_structured(narrative)
    structured = {**regex_structured, **json_structured}
    has_trigger = _has_entry_trigger(narrative, structured)
    has_risk = _has_invalidation_and_target(narrative, structured)
    rr = _extract_rr(narrative)

    extracted = {
        "has_entry_trigger": has_trigger,
        "has_invalidation_and_target": has_risk,
        "extracted_rr": rr,
        "structured": structured,
    }

    missing = []
    if not has_trigger:
        missing.append("ENTRY_TRIGGER (FVG / Order Block / liquidity sweep)")
    if not has_risk:
        missing.append("INVALIDATION + TARGET")

    # Logic check: if an R:R number is present it must meet MIN_RR
    import config
    if rr is not None and rr < config.MIN_RR:
        missing.append(f"R:R {rr} is below configured minimum {config.MIN_RR}")

    if missing:
        feedback = (
            "LTF Entry gate failed. You MUST end the stage with:\n"
            "ENTRY_TRIGGER: <FVG or Order Block description + timeframe>\n"
            "INVALIDATION: <price or structure level for the stop>\n"
            "TARGET: <draw-on-liquidity target>\n\n"
            f"Problems found: {', '.join(missing)}.\n"
            "If no clean trigger exists, explicitly say so — that is a valid "
            "outcome and the chain will stop cleanly."
        )
        return GateResult(
            passed=False,
            reason=f"LTF Entry gate failed — {', '.join(missing)}",
            extracted=extracted,
            feedback=feedback,
        )

    return GateResult(
        passed=True,
        reason="LTF Entry gate passed: trigger + invalidation + target present.",
        extracted=extracted,
    )


def gate_confluence(narrative: str, tool_results: list | None = None) -> GateResult:
    json_structured = parse_structured_output("risk_exec", narrative) or {}
    regex_structured = parse_structured(narrative)
    structured = {**regex_structured, **json_structured}
    score = _confluence_score(narrative, structured)
    extracted = {
        "confluence_score": score,
        "structured": structured,
    }

    if score >= 3:
        return GateResult(
            passed=True,
            reason=f"Confluence bar met (score {score}/4). Trade decision is allowed.",
            extracted=extracted,
        )

    feedback = (
        f"Confluence bar not met (score {score}/4). "
        "You must NOT call place_paper_trade. "
        "Log a WATCH or NO_SETUP analysis and explain which pillars are missing. "
        "Emit: CONFLUENCE_SCORE: {0-4} and DECISION: WATCH|NO_SETUP"
    )
    return GateResult(
        passed=False,
        reason=f"Confluence bar not met (score {score}/4).",
        extracted=extracted,
        feedback=feedback,
    )


def gate_liquidity_sequencing(narrative: str, tool_results: list | None = None) -> GateResult:
    """
    Gate for prompts/forward_test/02_draw_on_liquidity — the FORWARD
    LIQUIDITY SEQUENCING ENGINE prompt. Not wired into STAGE_GATES'
    default 4-stage chain yet (that still runs the generic htf_bias/
    timing/ltf_entry/risk_exec prompts hardcoded in harness/chained_loop.py) —
    this is ready to call directly, or to wire in once run_prompt_set
    actually drives per-file staged execution instead of just listing
    filenames.
    """
    seq = parse_sequencing_structured(narrative)
    extracted = {"sequencing": seq}

    missing = []
    if seq.get("htf_directional_bias") is None:
        missing.append("HTF_DIRECTIONAL_BIAS (BULLISH/BEARISH/UNCLEAR)")
    if seq.get("price_location") is None:
        missing.append("PRICE_LOCATION (PREMIUM/EQUILIBRIUM/DISCOUNT)")
    if seq.get("first_liquidity_event") is None:
        missing.append("FIRST_LIQUIDITY_EVENT (BSL/SSL/UNCLEAR)")
    if seq.get("first_liquidity_confidence") is None:
        missing.append("FIRST_LIQUIDITY_CONFIDENCE (HIGH/MEDIUM/LOW)")
    if not seq.get("buy_side_pools"):
        missing.append("BUY_SIDE_POOLS (at least one numbered pool)")
    if not seq.get("sell_side_pools"):
        missing.append("SELL_SIDE_POOLS (at least one numbered pool)")
    if not seq.get("invalidation"):
        missing.append("INVALIDATION")
    if not seq.get("post_sweep_next_draws_filled"):
        missing.append("POST-SWEEP DECISION TREE with at least one NEXT_DRAW filled in "
                        "(not left blank)")

    # Logic check: UNCLEAR sequencing paired with HIGH confidence is contradictory
    if (seq.get("first_liquidity_event", "").upper() == "UNCLEAR"
            and seq.get("first_liquidity_confidence", "").upper() == "HIGH"):
        missing.append("FIRST_LIQUIDITY_EVENT is UNCLEAR but FIRST_LIQUIDITY_CONFIDENCE "
                        "is HIGH — contradictory, pick one")

    if missing:
        feedback = (
            "Liquidity Sequencing gate failed. Emit the exact structured block "
            "from your instructions: HTF_DIRECTIONAL_BIAS, PRICE_LOCATION, "
            "FIRST_LIQUIDITY_EVENT, FIRST_LIQUIDITY_CONFIDENCE, at least one "
            "BUY_SIDE_POOLS and one SELL_SIDE_POOLS entry, an INVALIDATION "
            "line, and a filled-in POST-SWEEP DECISION TREE (at least one "
            "NEXT_DRAW = <value>, not left blank).\n\n"
            f"Missing or unclear: {', '.join(missing)}."
        )
        return GateResult(
            passed=False,
            reason=f"Liquidity Sequencing gate failed — missing: {', '.join(missing)}",
            extracted=extracted,
            feedback=feedback,
        )

    return GateResult(
        passed=True,
        reason=(
            f"Liquidity sequencing locked: {seq['first_liquidity_event']} first "
            f"({seq['first_liquidity_confidence']} confidence), price in "
            f"{seq['price_location']}."
        ),
        extracted=extracted,
    )


STAGE_GATES = {
    "htf_bias": gate_htf_bias,
    "timing": gate_timing,
    "ltf_entry": gate_ltf_entry,
    "confluence": gate_confluence,
    "liquidity_sequencing": gate_liquidity_sequencing,
}


# ---------------------------------------------------------------------------
# Generic fallback gate for file-based prompt-set stages (00/01/03/04/05/06
# and legacy-format 02s) that don't have a bespoke gate above. Instead of
# hand-writing a gate per stage file — which drifts out of sync the moment
# someone edits a prompt's Required Output block — this parses the field
# names straight out of the stage file's OWN ```text fenced template and
# checks the response actually filled each one in. The gate and the prompt
# can never disagree about what's required, because they read the same
# source. Not used for the liquidity-sequencing prompt (no fence, and it
# already has a purpose-built gate above).
# ---------------------------------------------------------------------------

_FENCED_BLOCK = re.compile(r"```text\s*\n(.*?)```", re.DOTALL)
_FIELD_LABEL = re.compile(r"^([A-Z][A-Z0-9_]*)\s*:")


def extract_required_fields(stage_prompt_text: str) -> list:
    """Field names declared in a stage file's fenced ```text Required
    Output block, e.g. ['PREV_MONTH_HIGH', 'PATH_OF_LEAST_RESISTANCE'].

    Skips bare section headers (a 'FIELD:' line with nothing after the
    colon, immediately followed by another FIELD: label) — those just
    introduce a sub-block (e.g. 'FIRST_LIQUIDITY_RACE:' before
    'BSL_CANDIDATE:') and have no scalar value of their own to check."""
    m = _FENCED_BLOCK.search(stage_prompt_text)
    if not m:
        return []
    lines = m.group(1).splitlines()
    fields = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        fm = _FIELD_LABEL.match(stripped)
        if not fm:
            continue
        field = fm.group(1)
        after_colon = stripped[fm.end():].strip()
        if after_colon:
            # inline content on the same line (even a placeholder like
            # <level> or FORWARD) -> a real field regardless of what follows
            fields.append(field)
            continue
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and not _FIELD_LABEL.match(lines[j].strip()):
            fields.append(field)
        # else: next non-blank line is itself a FIELD: label -> this line
        # was just a section header, not a field requiring its own value.
    return fields


def _field_value(narrative: str, field: str) -> str | None:
    """Value for FIELD, whether written 'FIELD: value' on one line or
    'FIELD:' with the value on the next non-empty line."""
    same_line = re.search(rf"{re.escape(field)}\s*:\s*(\S.*)", narrative)
    if same_line:
        val = same_line.group(1).strip()
        if val not in ("", "<", "...", "N/A"):
            return val
    next_line = re.search(rf"{re.escape(field)}\s*:\s*\n\s*(\S.+)", narrative)
    if next_line:
        val = next_line.group(1).strip()
        if val:
            return val
    return None


def extract_generic_facts(narrative: str, required_fields: list) -> dict:
    """Best-effort value for every declared field — used to build the
    compact 'locked so far' context handed to later stages."""
    facts = {}
    for field in required_fields:
        val = _field_value(narrative, field)
        if val:
            facts[field] = val
    return facts


def gate_generic_required_fields(narrative: str, required_fields: list) -> GateResult:
    if not required_fields:
        # Stage file has no fenced template to check against — pass
        # through rather than blocking on something we can't verify.
        return GateResult(passed=True, reason="No fenced Required Output block to check against.")

    missing = [f for f in required_fields if _field_value(narrative, f) is None]
    if missing:
        feedback = (
            f"Your response is missing values for fields this stage's own template "
            f"requires: {', '.join(missing)}. Emit every field from the Required "
            f"Output block with a real value, not a placeholder or blank."
        )
        return GateResult(
            passed=False,
            reason=f"Missing required fields: {', '.join(missing)}",
            extracted={"facts": extract_generic_facts(narrative, required_fields)},
            feedback=feedback,
        )
    return GateResult(
        passed=True,
        reason=f"All {len(required_fields)} template-declared fields present.",
        extracted={"facts": extract_generic_facts(narrative, required_fields)},
    )
