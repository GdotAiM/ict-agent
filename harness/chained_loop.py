"""
Staged Prompt-Chaining loop for the ICT Agent — with full Output Validation.

Implements the Udacity "Prompt Chaining + Gate Checks" pattern, including:

  * Sequential stages (HTF Bias → Timing → LTF Entry → Risk/Exec)
  * Programmatic gate checks between stages
  * On gate failure: retry the same stage with the failure reason injected
    back into the prompt (up to GATE_MAX_RETRIES times)
  * Hard stop after retries are exhausted → disciplined no_setup narrative

Each stage:
  - receives accumulated context from prior stages
  - is restricted to its allowed tool subset
  - is instructed to emit a short structured block for reliable parsing
  - is validated by a pure-Python gate before the next stage is allowed
"""
from __future__ import annotations
import config
from harness.kernel import PluginKernel
from harness.plugin import ModelAdapterPlugin
from harness.context import RunContext
from harness.session_log import SessionLog
from memory.metrics import record_stage_metrics
from memory.store import get_similar_setups, get_cross_symbol_similar
from memory.session_state import get_session_state
from harness.token_tracker import TokenTracker, BudgetExceeded
from harness.narrative_compressor import compress_narratives
from harness.observability import trace_stage, trace_tool, trace_llm_call, _get_client
from agent.gates import (
    gate_htf_bias, gate_timing, gate_ltf_entry, gate_confluence, GateResult,
)


# Tools allowed in each stage (names must match tool plugins)
STAGE_TOOLS = {
    "htf_bias": [
        "get_candles_summary", "get_market_structure", "get_liquidity_pools",
        "get_pd_array", "get_recent_context", "search_ict_knowledge", "get_economic_calendar",
    ],
    "timing": [
        "get_kill_zone", "get_recent_context", "log_analysis", "get_economic_calendar",
        "search_ict_knowledge",
    ],
    "ltf_entry": [
        "get_candles_summary", "get_fair_value_gaps", "get_order_blocks",
        "get_liquidity_pools", "get_market_structure",
        "search_ict_knowledge",
    ],
    "risk_exec": [
        # log_trade is NOT a directly callable tool — place_paper_trade's
        # handler logs the trade internally on success. Listing it here
        # would be a dead entry (silently dropped by _filter_tools).
        "place_paper_trade", "log_analysis",
        "get_recent_context",
        "search_ict_knowledge",
    ],
}

STAGE_ORDER = ["htf_bias", "timing", "ltf_entry", "risk_exec"]

# Structured output contracts the model is told to emit at the end of each stage
STAGE_STRUCTURED_HINTS = {
    "htf_bias": """
At the end of your response, output this exact JSON (no markdown fences):
{"bias": "BEARISH", "draw_on_liquidity": "SSL at {price} or BSL at {price}", "pd_array": "PREMIUM"}
Valid bias: BULLISH, BEARISH, RANGING. Valid pd_array: PREMIUM, DISCOUNT, EQUILIBRIUM.
""",
    "timing": """
At the end of your response, output this exact JSON (no markdown fences):
{"kill_zone": "NY_AM", "in_kill_zone": true}
Valid kill_zone: LONDON, NY_AM, NY_PM, ASIAN, OUTSIDE.
""",
    "ltf_entry": """
At the end of your response, output this exact JSON (no markdown fences):
{"entry_trigger": "NONE", "invalidation": "<price-level-or-NONE>", "target": "<price-level-or-NONE>"}
Set entry_trigger="NONE" if no clean trigger exists.
""",
    "risk_exec": """
At the end of your response, output this exact JSON (no markdown fences):
{"confluence_score": 3, "decision": "NO_SETUP"}
confluence_score: 0-4. decision: TRADE, WATCH, or NO_SETUP.
""",
}

STAGE_PROMPTS = {
    "htf_bias": """STAGE 1 — HIGHER TIMEFRAME BIAS (mandatory first).

Work only with HTF candles. Your job this stage:

1. Call get_market_structure on the HTF to determine trend via BOS / CHoCH.
2. Call get_liquidity_pools to locate BSL and SSL and state where price is
   most likely being drawn next.
3. Call get_pd_array to locate equilibrium of the current dealing range and
   state whether price is in premium or discount.
4. MUST call search_ict_knowledge(query="draw on liquidity weekly profile premium discount", stage="htf_bias", top_k=3) to ground your bias argument in ICT doctrine.
   Use the retrieved passages to strengthen your reasoning -- reference specific ICT principles when they apply.
5. Pull get_recent_context to avoid repeating past mistakes.

IMPORTANT: After you have received ALL tool results, write your complete Stage 1 analysis as a coherent narrative. Then end your response with these THREE lines EXACTLY as shown:

BIAS: BULLISH|BEARISH|RANGING
DRAW_ON_LIQUIDITY: <describe where price is being drawn — BSL, SSL, equal highs/lows>
PD_ARRAY: PREMIUM|DISCOUNT|EQUILIBRIUM

Do NOT call any more tools after writing the BIAS line. Do NOT discuss LTF entries, FVGs, or order blocks yet. Do NOT place a trade. Write your narrative now.""",

    "timing": """STAGE 2 — TIMING & CONTEXT.

You already locked HTF bias. Now:

1. Call get_kill_zone and state whether we are inside London, NY AM, NY PM,
   or outside the high-probability windows.
2. MUST call search_ict_knowledge(query="kill zone session dynamics london ny algorithmic delivery", stage="timing", top_k=2) to ground your timing assessment in ICT time-based theory.
3. Review any recent context if useful.

After you have all tool results, write a short narrative stating kill-zone status and whether the HTF bias setup is worth pursuing right now. Reference ICT teaching on time-based price delivery when justifying your assessment. If outside kill zones, only proceed if you can explicitly justify an exceptional / high-conviction reason.

Then end your response with:
KILL_ZONE: LONDON|NY_AM|NY_PM|ASIAN|OUTSIDE

Do NOT call any more tools after writing KILL_ZONE. Do NOT yet describe LTF entry triggers. Do NOT place a trade.""",

    "ltf_entry": """STAGE 3 — LTF ENTRY MODEL.

HTF bias and timing are confirmed. Now look for the entry trigger on the
entry timeframe:

1. After a liquidity sweep in the direction of the HTF bias, look for a
   Fair Value Gap (get_fair_value_gaps) or Order Block (get_order_blocks).
   2. MUST call search_ict_knowledge(query="order block entry model displacement fair value gap", stage="ltf_entry", top_k=3)
      Verify your entry model against ICT teaching before writing the structured output.
2. State a clear invalidation level (stop) beyond the sweep / OB.
3. State a draw-on-liquidity target that satisfies minimum reward:risk.

If no clean trigger exists, set ENTRY_TRIGGER: NONE — that is a valid outcome.

After you have all tool results, write your analysis and end with these exact lines:
ENTRY_TRIGGER: <FVG/OB description> | NONE
INVALIDATION: <price level for stop>
TARGET: <draw-on-liquidity target>

Do NOT call any more tools after writing these lines. Do NOT place a trade.""",

    "risk_exec": """STAGE 4 — RISK, CONFLUENCE & FINAL DECISION.

You have completed the full top-down chain. Now:

1. Score the confluence bar (structure + liquidity + PD array + LTF trigger).
   Only a score of 3 or 4 allows a trade.
2. FIRST, write these exact lines PLAIN TEXT (no code fences):
CONFLUENCE_SCORE: 0|1|2|3|4
DECISION: TRADE|WATCH|NO_SETUP
3. Then, based on your decision:
   - If TRADE: call place_paper_trade with explicit stop and target
   - If WATCH/NO_SETUP: call log_analysis with decision="watch" or "no_setup"
   Always include your narrative in log_analysis.

IMPORTANT: Write the structured lines directly, not inside code blocks.
Be disciplined. Paper account only. Prefer a clean "no_setup" over a forced trade.""",
}


def _filter_tools(kernel: PluginKernel, allowed_names: list[str]) -> list[dict]:
    all_schemas = kernel.tool_schemas()
    allowed = set(allowed_names)
    return [s for s in all_schemas if s.get("name") in allowed]


def _detect_compression(swing_lows: list, swing_highs: list, price: float,
                         nearest_liquidity: float | None = None) -> dict:
    """Detect pre-sweep compression in swing structure.

    Returns dict with:
      - ratio: how much tighter the recent swings are vs prior (higher = more compressed)
      - direction: 'down' if lows descending, 'up' if highs ascending
      - prox_pct: distance from price to nearest liquidity as percentage
      - prox_alert: True if within 5% of nearest liquidity pool
      - sweep_alert: True if compression > 2x AND price near liquidity
    """
    result = {"ratio": 0.0, "direction": "", "prox_pct": 999.0, "prox_alert": False, "sweep_alert": False}

    # --- Compression from swing lows ---
    low_vals = [float(x[1]) for x in swing_lows[-4:] if isinstance(x[1], (int, float))]
    if len(low_vals) >= 4:
        old_span = abs(low_vals[0] - low_vals[1])
        new_span = abs(low_vals[2] - low_vals[3])
        if new_span > 0 and old_span > 0:
            result["ratio"] = round(old_span / new_span, 1)

    # --- Direction from swing highs ---
    high_vals = [float(x[1]) for x in swing_highs[-4:] if isinstance(x[1], (int, float))]
    if len(high_vals) >= 3:
        if high_vals[-1] < high_vals[-2] < high_vals[-3]:
            result["direction"] = "down"
        elif high_vals[-1] > high_vals[-2] > high_vals[-3]:
            result["direction"] = "up"

    # --- Proximity to liquidity ---
    if nearest_liquidity and nearest_liquidity > 0 and price > 0:
        result["prox_pct"] = round(abs(price - nearest_liquidity) / nearest_liquidity * 100, 2)
        result["prox_alert"] = result["prox_pct"] < 5.0
        if result["ratio"] >= 2.0 and result["prox_alert"]:
            result["sweep_alert"] = True

    return result


def _synthesize_htf_narrative(tool_results: list) -> str:
    """Fallback: build structured narrative from tool results when the model
    returns only whitespace after collecting all data (a known pattern with
    agnes-2.5-flash on Windows via the Node bridge)."""
    by_name = {r.get("name", ""): r.get("result", {}) for r in tool_results}

    structure = by_name.get("get_market_structure", {})
    pd_data = by_name.get("get_pd_array", {})
    liq = by_name.get("get_liquidity_pools", {})

    trend = (structure.get("trend") or "").upper()
    bos = structure.get("last_event", "")
    price = pd_data.get("current_price")
    zone = (pd_data.get("zone") or "UNKNOWN").upper()
    eq = pd_data.get("equilibrium")
    bsl_levels = [h[1] for h in (liq.get("bsl", {}).get("raw_highs", [])) if len(h) > 1]
    ssl_levels = [l[1] for l in (liq.get("ssl", {}).get("raw_lows", [])) if len(l) > 1]
    nearest_bsl = min(bsl_levels) if bsl_levels else None
    nearest_ssl = max(ssl_levels) if ssl_levels else None

    bias_word = trend if trend in ("BULLISH", "BEARISH") else "RANGING"
    draw_on = f"SSL at {nearest_ssl:.2f}" if nearest_ssl else "BSL at " + (f"{nearest_bsl:.2f}" if nearest_bsl else "liquidity")
    price_str = f"{price:.2f}" if price is not None else "?"
    eq_str = f"{eq:.2f}" if eq is not None else "?"

    lines = [
        f"[HTF Analysis] Trend: {bias_word}. BOS at {bos}.",
        f"Price at {price_str} in {zone} zone (equilibrium {eq_str}).",
        f"Draw-on liquidity: {draw_on}.",
        f"BIAS: {bias_word}",
        f"DRAW_ON_LIQUIDITY: {draw_on}",
        f"PD_ARRAY: {zone}",
    ]
    return "\n\n".join(lines)


def _synthesize_ltf_narrative(tool_results: list, htf_bias_text: str = "") -> str:
    """Build structured LTF narrative from tool results.
    Handles both conventional triggers AND Judas-sweep-displacement patterns
    where the model returns whitespace instead of committing to output."""
    by_name = {r.get("name", ""): r.get("result", {}) for r in tool_results}

    # Get HTF context if provided
    htf_trend = ""
    htf_price = ""
    htf_eq = ""
    if htf_bias_text:
        import re
        m = re.search(r'Price at ([\d.]+)', htf_bias_text)
        if m: htf_price = m.group(1)
        m = re.search(r'in (\w+) zone', htf_bias_text, re.I)
        if m: pass  # zone captured below
        m = re.search(r'equilibrium ([\d.]+)', htf_bias_text)
        if m: htf_eq = m.group(1)
        m = re.search(r'Trend: (\w+)', htf_bias_text)
        if m: htf_trend = m.group(1)

    pd_data = by_name.get("get_pd_array", {})
    liq = by_name.get("get_liquidity_pools", {})
    fvgs = by_name.get("get_fair_value_gaps", {}).get("fvgs", [])
    obs = by_name.get("get_order_blocks", {}).get("order_blocks", [])
    structure = by_name.get("get_market_structure", {})

    price = pd_data.get("current_price", 0)
    zone = (pd_data.get("zone") or "UNKNOWN").upper()
    eq = pd_data.get("equilibrium", 0)
    trend = (structure.get("trend") or "").upper()

    # Find nearest SSL/BSL
    ssl_levels = sorted([l[1] for l in (liq.get("ssl", {}).get("raw_lows", [])) if len(l) > 1])
    bsl_levels = sorted([h[1] for h in (liq.get("bsl", {}).get("raw_highs", [])) if len(h) > 1], reverse=True)
    nearest_ssl = ssl_levels[-1] if ssl_levels else None
    nearest_bsl = bsl_levels[0] if bsl_levels else None

    # Check for Judas sweep pattern: price below SSL with displacement FVGs above
    ssl_swept = False
    sweep_depth = 0
    if nearest_ssl and price and price < nearest_ssl:
        sweep_depth = nearest_ssl - price
        if sweep_depth > 0:
            ssl_swept = True

    # --- Pre-sweep compression detection ---
    # Uses raw swing data from market_structure tool to detect coiling before the sweep
    swing_lows = by_name.get("get_market_structure", {}).get("swing_lows", [])
    swing_highs = by_name.get("get_market_structure", {}).get("swing_highs", [])
    nearest_liq = nearest_ssl if nearest_ssl else nearest_bsl
    compression = _detect_compression(swing_lows, swing_highs, price, nearest_liquidity=nearest_liq)
    prox_pct = compression.get("prox_pct", 999.0)

    # Find FVGs near/at price (could be displacement-created)
    # Wider threshold for LTF — displacement can create gaps further away
    # Use adaptive threshold: 0.5% of price for indices, 0.05% for forex
    fvg_threshold = price * 0.005 if price > 1000 else price * 0.005
    nearby_fvgs = []
    for fvg in fvgs:
        top = fvg.get("top", 0)
        bot = fvg.get("bottom", 0)
        mid = (top + bot) / 2
        dist = abs(mid - price) if price else 9999
        if dist < fvg_threshold:
            nearby_fvgs.append((mid, top, bot, fvg.get("type",""), fvg.get("filled", False)))

    # Find OBs near price (use same adaptive threshold)
    nearby_obs = []
    for ob in obs:
        top = ob.get("top", 0)
        bot = ob.get("bottom", 0)
        mid = (top + bot) / 2
        dist = abs(mid - price) if price else 9999
        if dist < fvg_threshold * 1.5:
            nearby_obs.append((mid, top, bot, ob.get("type",""), ob.get("displacement_at","")))

    # Build narrative
    lines = []

    # --- Pre-sweep alert: compression + proximity to liquidity ---
    if compression.get("sweep_alert") and not ssl_swept:
        lines.append(f"[PRE-SWEEP ALERT]")
        lines.append(f"Swing compression detected: {compression['ratio']:.1f}x tightening.")
        lines.append(f"Price at {price:.2f} is {prox_pct:.1f}% from {'SSL' if nearest_ssl else 'BSL'} at {nearest_ssl or nearest_bsl:.2f}.")
        direction = compression.get('direction', '')
        if trend == 'BEARISH':
            lines.append(f"Structure: {direction.upper()} swings coiling → expect downward displacement sweep of SSL.")
        elif trend == 'BULLISH':
            lines.append(f"Structure: {direction.upper()} swings coiling → expect upward displacement sweep of BSL.")
        lines.append(f"STATUS: AWAITING SWEEP — do not enter yet. Watch for displacement candle after the sweep.")
        lines.append(f"ENTRY_TRIGGER: PENDING (sweep not yet confirmed)")
        lines.append(f"INVALIDATION: N/A")
        lines.append(f"TARGET: {'SSL at ' + f'{nearest_ssl:.2f}' if nearest_ssl else 'BSL at ' + f'{nearest_bsl:.2f}'}")
        lines.append(f"PD_ARRAY: {zone}")
        return "\n\n".join(lines)

    if ssl_swept and nearby_fvgs:
        # JUDAS SWEEP PATTERN DETECTED
        lines.append(f"[JUDAS SWEEP PATTERN]")
        lines.append(f"Swept SSL at {nearest_ssl:.2f}, price now at {price:.2f} ({sweep_depth:.1f} pts below).")
        lines.append(f"Bullish displacement created fresh FVGs above:")
        for mid, top, bot, ftype, filled in sorted(nearby_fvgs, key=lambda x: abs(x[0]-price)):
            status = "FILLED" if filled else "OPEN"
            lines.append(f"  {top:.1f}–{bot:.1f} [{status}] mid={mid:.1f}")
        lines.append(f"Wait for retrace into these FVGs for short entry.")
        lines.append(f"ENTRY_TRIGGER: Bullish displacement FVG {nearby_fvgs[0][2]:.1f}–{nearby_fvgs[0][1]:.1f} (post-SSL sweep)")
        lines.append(f"INVALIDATION: Above {nearby_fvgs[0][1]+5:.1f}")
        lines.append(f"TARGET: {nearest_ssl:.2f} (SSL) / {ssl_levels[-2] if len(ssl_levels)>1 else 'next support'}")
        lines.append(f"BIAS: {htf_trend if htf_trend else trend}")
    elif nearby_fvgs or nearby_obs:
        # CONVENTIONAL PATTERN
        lines.append(f"[LTF Analysis] Price at {price:.2f} in {zone}.")
        if nearby_fvgs:
            lines.append(f"Nearby FVGs:")
            for mid, top, bot, ftype, filled in sorted(nearby_fvgs, key=lambda x: abs(x[0]-price))[:3]:
                status = "FILLED" if filled else "OPEN"
                lines.append(f"  {top:.1f}–{bot:.1f} [{status}] {ftype}")
            lines.append(f"ENTRY_TRIGGER: FVG at {nearby_fvgs[0][2]:.1f}–{nearby_fvgs[0][1]:.1f}")
            lines.append(f"INVALIDATION: Above {nearby_fvgs[0][1]+5:.1f}")
        if nearby_obs:
            lines.append(f"Nearby OBs:")
            for mid, top, bot, otype, disp in sorted(nearby_obs, key=lambda x: abs(x[0]-price))[:2]:
                lines.append(f"  {top:.1f}–{bot:.1f} [{otype}] disp@{disp}")
            if not lines[-1].startswith("ENTRY"):
                lines.append(f"ENTRY_TRIGGER: OB at {nearby_obs[0][2]:.1f}–{nearby_obs[0][1]:.1f}")
                lines.append(f"INVALIDATION: Above {nearby_obs[0][1]+5:.1f}")
        lines.append(f"TARGET: {nearest_ssl:.2f}" if nearest_ssl else f"TARGET: next liquidity pool")
    else:
        # NO TRIGGER
        lines.append(f"[LTF Analysis] Price at {price:.2f} in {zone}. No trigger in range.")
        lines.append(f"ENTRY_TRIGGER: NONE")
        lines.append(f"INVALIDATION: N/A")
        lines.append(f"TARGET: {nearest_ssl:.2f}" if nearest_ssl else "TARGET: N/A")

    lines.append(f"PD_ARRAY: {zone}")
    return "\n\n".join(lines)


def _run_single_stage(
    kernel: PluginKernel,
    adapter: ModelAdapterPlugin,
    system_prompt: str,
    stage_name: str,
    stage_user_message: str,
    messages: list,
    session: SessionLog,
    ctx: RunContext,
    max_iters: int,
    accumulated_narratives: list[str] | None = None,
    token_tracker: TokenTracker | None = None,
) -> tuple[str, list]:
    """
    Runs one stage of tool-calling until the model stops or max_iters.
    Returns (final_text_for_stage, updated_messages).
    Applies a synthesis fallback when the model returns whitespace-only
    after tool results but before committing to structured output.
    """
    allowed = STAGE_TOOLS.get(stage_name, [])
    tools = _filter_tools(kernel, allowed)
    token_tracker = token_tracker or TokenTracker()

    session.append("stage_start", {
        "stage": stage_name,
        "allowed_tools": allowed,
    })

    messages.append({"role": "user", "content": stage_user_message})

    # Trim stale head of message history to bounded window
    _trim_messages(messages, max_window=config.MAX_MESSAGE_WINDOW)

    stage_text = ""
    collected_tool_results: list = []
    for step in range(max_iters):
        response = trace_llm_call(
            adapter, system_prompt, tools, messages,
            model_name=adapter.name,
            extra_tags={"stage": stage_name},
        )
        # Trim after each turn to prevent unbounded growth within a stage
        _trim_messages(messages, max_window=config.MAX_MESSAGE_WINDOW)
        messages.append(adapter.to_assistant_message(response))

        text = adapter.extract_text(response)
        calls = adapter.extract_tool_calls(response)
        session.append("model_response", {
            "stage": stage_name,
            "step": step,
            "text": text,
            "tool_calls": [c["name"] for c in calls],
        })

        # Token budget enforcement
        try:
            token_tracker.add(response)
        except BudgetExceeded as exc:
            session.append("budget_exceeded", {
                "stage": stage_name,
                "step": step,
                "reason": str(exc),
                "stage_tokens": token_tracker.stage_used(),
                "cycle_tokens": token_tracker.cycle_used(),
            })
            # Truncate response to force a stop — inject budget warning
            if text.strip():
                text += f"\n\n[BUDGET ALERT: {exc} — be concise in any follow-up]"
            break

        # Only keep non-empty text - agnes sometimes returns "" after tool results
        stripped = text.strip()
        if stripped:
            stage_text = text

        if adapter.is_done(response):
            break

        results = []
        for call in calls:
            if call["name"] not in allowed:
                result = {
                    "error": f"tool '{call['name']}' not permitted in stage '{stage_name}'"
                }
            else:
                _tool_input = call.get("input", {}) or {}
                # trace_tool must never receive 'symbol' — it takes it as a
                # positional kwarg and **_tool_input would duplicate it.
                # kernel.dispatch receives the ORIGINAL call["input"] below,
                # so handlers like log_analysis/get_recent_context still get
                # symbol from there.
                _trace_symbol = getattr(ctx, "symbol", "UNKNOWN")
                if "symbol" in _tool_input:
                    _trace_symbol = _tool_input["symbol"]
                with trace_tool(call["name"], symbol=_trace_symbol):
                    session.append("tool_call", {
                        "stage": stage_name,
                        "name": call["name"],
                        "input": call["input"],
                    })
                    result = kernel.dispatch(call["name"], call["input"], ctx)
            session.append("tool_result", {
                "stage": stage_name,
                "name": call["name"],
                "result": result,
            })
            results.append({"tool_use_id": call["id"], "content": result})
            collected_tool_results.append({"name": call["name"], "result": result})

        messages.append(adapter.to_tool_result_message(results))

    # Synthesis fallback: if the model returned no substantive text despite
    # collecting tool results, build the structured narrative from the data.
    # This handles the known pattern where agnes-2.5-flash returns only
    # whitespace after the final tool round instead of committing to output.
    if collected_tool_results:
        has_structured = False
        if stage_name == "htf_bias":
            from agent.gates import parse_structured
            s = parse_structured(stage_text)
            has_structured = bool(s.get("bias") and s.get("draw_on_liquidity") and s.get("pd_array"))
        elif stage_name == "ltf_entry":
            from agent.gates import parse_structured
            s = parse_structured(stage_text)
            has_structured = bool(s.get("entry_trigger", "").strip() not in ("", "NONE") or s.get("invalidation"))
        if not has_structured:
            if stage_name == "htf_bias":
                stage_text = _synthesize_htf_narrative(collected_tool_results)
                session.append("model_response", {
                    "stage": stage_name,
                    "step": "synthesized",
                    "text": stage_text,
                    "tool_calls": [],
                    "synthesized": True,
                })
            elif stage_name == "ltf_entry":
                # Pass accumulated HTF narrative as context so synthesis
                # can detect Judas-sweep-displacement patterns
                htf_context = "\n".join(accumulated_narratives) if accumulated_narratives else ""
                stage_text = _synthesize_ltf_narrative(collected_tool_results, htf_context)
                session.append("model_response", {
                    "stage": stage_name,
                    "step": "synthesized",
                    "text": stage_text,
                    "tool_calls": [],
                    "synthesized": True,
                })

    session.append("stage_end", {"stage": stage_name, "narrative": stage_text})
    return stage_text, messages


def _run_stage_with_retries(
    kernel: PluginKernel,
    adapter: ModelAdapterPlugin,
    system_prompt: str,
    stage_name: str,
    base_prompt: str,
    messages: list,
    session: SessionLog,
    ctx: RunContext,
    max_iters: int,
    gate_fn,
    accumulated_narratives: list[str],
    token_tracker: TokenTracker | None = None,
) -> tuple[str, list, GateResult, bool]:
    """
    Execute a stage, run its gate, and on failure retry up to GATE_MAX_RETRIES
    times with the gate's feedback injected into the prompt.

    Returns:
        (final_stage_text, updated_messages, final_gate_result, should_continue)
    """
    max_retries = getattr(config, "GATE_MAX_RETRIES", 2)
    attempt = 0
    stage_text = ""
    gate = GateResult(passed=False, reason="not run")
    token_tracker = token_tracker or TokenTracker()
    token_tracker.reset_stage()  # reset per-stage counter for this stage

    while attempt <= max_retries:
        # Build the prompt for this attempt
        prompt = base_prompt
        if attempt > 0 and gate.feedback:
            prompt = (
                base_prompt
                + "\n\n=== GATE CHECK FAILED (attempt "
                + f"{attempt}/{max_retries}) ===\n"
                + "The previous output did not pass validation.\n"
                + "Failure reason and required corrections:\n"
                + gate.feedback
                + "\n\nRe-do this stage carefully. Use the tools again if needed "
                + "You MUST explicitly write out the required structured output lines (BIAS, DRAW_ON_LIQUIDITY, PD_ARRAY etc.) in your text response — do not rely on tool results alone."
            )
            session.append("gate_retry", {
                "stage": stage_name,
                "attempt": attempt,
                "reason": gate.reason,
                "feedback_injected": True,
            })

        # Always append the structured-output hint
        prompt += "\n" + STAGE_STRUCTURED_HINTS.get(stage_name, "")

        stage_text, messages = _run_single_stage(
            kernel, adapter, system_prompt, stage_name, prompt,
            messages, session, ctx, max_iters,
            token_tracker=token_tracker,
        )

        gate = gate_fn(stage_text)
        session.append("gate_check", {
            "stage": stage_name,
            "attempt": attempt,
            "passed": gate.passed,
            "reason": gate.reason,
            "extracted": gate.extracted,
            "soft": gate.soft,
        })
        try:
            record_stage_metrics(
                session, symbol=getattr(session, "session_id", "").split("_")[0],
                mode="chained", stage=stage_name, narrative=stage_text,
                gate_passed=gate.passed, gate_reason=gate.reason,
                retries=attempt,
            )
        except Exception:
            pass

        if gate.passed:
            return stage_text, messages, gate, True

        # Soft gate that failed: we still allow continuation after logging
        if gate.soft and attempt >= max_retries:
            session.append("gate_soft_override", {
                "stage": stage_name,
                "reason": gate.reason,
            })
            return stage_text, messages, gate, True

        attempt += 1

    # Retries exhausted
    hard_stop = getattr(config, "GATE_HARD_STOP_ON_EXHAUST", True)
    if hard_stop and not gate.soft:
        return stage_text, messages, gate, False
    # Degraded continue
    session.append("gate_degraded", {
        "stage": stage_name,
        "reason": gate.reason,
    })
    return stage_text, messages, gate, True



def _trim_messages(messages: list, max_window: int) -> None:
    """Trim message history to a bounded sliding window.

    Keeps: system prompt (index 0) + last N user-assistant pairs.
    Tool-result messages inside the kept region are preserved; older ones
    are dropped. This prevents unbounded growth within a single stage's
    tool-call loop without losing the most recent reasoning.
    """
    if len(messages) <= max_window * 2 + 1:
        return
    # Always keep the system prompt (first message)
    kept = [messages[0]]
    # Walk backwards from the end, keeping pairs of (user/tool_result) or
    # (assistant/tool_result) — actually we just keep the tail up to max_window
    # full turns (each turn = assistant message + any following tool results).
    # Simpler: keep last max_window*2 entries + the system prompt.
    tail = messages[-(max_window * 2):]
    # Ensure we start with an assistant message in the tail so it pairs cleanly
    if tail and tail[0].get("role") == "user":
        tail = tail[1:]
    kept.extend(tail)
    messages.clear()
    messages.extend(kept)


def _compress_narratives_for_stage(accumulator: list[str]) -> str:
    """Lightweight non-LLM compression: extract only key-value lines.

    Used as fallback when no adapter is available (or to avoid an extra LLM
    call on retry loops). Produces ~150 tokens from ~2000 of raw narrative.
    """
    lines = []
    for block in accumulator:
        for line in block.splitlines():
            stripped = line.strip()
            # Keep lines that are KEY: VALUE format (structured output)
            if ":" in stripped and not stripped.startswith("#") and not stripped.startswith("-"):
                # Only keep lines that look like our structured fields
                upper = stripped.upper()
                if any(kw in upper for kw in [
                    "BIAS:", "DRAW_ON_LIQUIDITY:", "PD_ARRAY:",
                    "KILL_ZONE:", "ENTRY_TRIGGER:", "INVALIDATION:",
                    "TARGET:", "CONFLUENCE_SCORE:", "DECISION:",
                    "STAGE",
                ]):
                    lines.append(stripped)
    return "\n".join(lines) if lines else ""


def _build_mag_context(symbol: str, session) -> str:
    """Build MAG context string from semantic recall + cross-cycle state."""
    lines = []

    # Cross-cycle session state (decisions, streaks, last scan time)
    try:
        state = get_session_state()
        state_summary = state.build_summary(symbol)
        if state_summary:
            lines.append(f"[SESSION STATE] {state_summary}")
    except Exception:
        pass

    # Same-symbol semantic recall
    similar = get_similar_setups(symbol, k=3, query_text=f"htf bias {symbol} market structure")
    if similar:
        lines.append(f"Relevant past setups for {symbol}:")
        for s in similar:
            lines.append(
                f"  - {s['ts'][:10]} | {s['bias']} | trigger={s['trigger_type']} | "
                f"zone={s['zone']} | decision={s['decision']} | sim={s['similarity']}"
            )

    # Cross-symbol recall
    cross = get_cross_symbol_similar(symbol, k=2, query_text=f"market structure bias liquidity")
    if cross:
        lines.append(f"Cross-symbol patterns:")
        for s in cross:
            lines.append(
                f"  - {s['symbol']} | {s['bias']} | trigger={s['trigger_type']} | "
                f"zone={s['zone']} | decision={s['decision']} | sim={s['similarity']}"
            )

    return chr(10).join(lines) if lines else ""

def run_chained(
    kernel: PluginKernel,
    adapter: ModelAdapterPlugin,
    system_prompt: str,
    user_message: str,
    session: SessionLog,
    ctx: RunContext | None = None,
) -> str:
    """
    Full ICT staged chain with gate checks + retry-with-feedback + MAG recall.
    Returns the final narrative (or an early-stop narrative if a hard gate
    exhausts its retries).
    """
    ctx = ctx or RunContext()
    messages: list = [{"role": "user", "content": user_message}]
    tracker = TokenTracker()

    # MAG: inject semantic recall into Stage 1 context
    symbol = getattr(ctx, "symbol", None) or "XAUUSD"
    mag_context = _build_mag_context(symbol, session)

    session.append("system_prompt", {"text": system_prompt})
    session.append("user_message", {"text": user_message})
    session.append("mounted_tools", {
        "names": kernel.list_tools(),
        "model_adapter": adapter.name,
        "mode": "chained",
        "gate_max_retries": getattr(config, "GATE_MAX_RETRIES", 2),
    })
    session.append("chain_start", {"stages": STAGE_ORDER, "budget": {
        "per_stage": config.TOKEN_BUDGET_PER_STAGE,
        "per_cycle": config.TOKEN_BUDGET_PER_CYCLE,
    }})

    accumulated_narratives: list[str] = []
    max_iters = 5  # Allow multiple tool-call rounds before final narrative
    brief = ""  # Compressed context passed between stages

    # ---------- Stage 1: HTF Bias ----------
    base1 = (
        STAGE_PROMPTS["htf_bias"]
        + f"\n\nOriginal request:\n{user_message}"
    )
    text1, messages, gate1, cont = _run_stage_with_retries(
        kernel, adapter, system_prompt, "htf_bias", base1,
        messages, session, ctx, max_iters,
        gate_htf_bias, accumulated_narratives,
        token_tracker=tracker,
    )
    accumulated_narratives.append(f"[STAGE 1 — HTF BIAS]\n{text1}")
    brief = _compress_narratives_for_stage(accumulated_narratives)
    if not cont:
        final = (
            f"CHAIN STOPPED at Stage 1 (HTF Bias) after retries exhausted.\n"
            f"Final gate reason: {gate1.reason}\n\n"
            f"Narrative so far:\n{text1}\n\n"
            f"Decision: NO_SETUP — higher-timeframe story could not be locked. "
            f"Standing aside is the correct ICT response."
        )
        session.append("final_narrative", {"text": final, "stopped_at": "htf_bias"})
        return final

    # ---------- Stage 2: Timing ----------
    base2 = (
        STAGE_PROMPTS["timing"]
        + (f"\n\n--- Prior stage summary ---\n{brief}\n" if brief else "")
    )
    text2, messages, gate2, cont = _run_stage_with_retries(
        kernel, adapter, system_prompt, "timing", base2,
        messages, session, ctx, max_iters,
        gate_timing, accumulated_narratives,
        token_tracker=tracker,
    )
    accumulated_narratives.append(f"[STAGE 2 — TIMING]\n{text2}")
    brief = _compress_narratives_for_stage(accumulated_narratives)
    # Timing is soft; we rarely hard-stop here, but the helper already handles it

    # ---------- Stage 3: LTF Entry ----------
    base3 = (
        STAGE_PROMPTS["ltf_entry"]
        + (f"\n\n--- Prior stage summary ---\n{brief}\n" if brief else "")
    )
    text3, messages, gate3, cont = _run_stage_with_retries(
        kernel, adapter, system_prompt, "ltf_entry", base3,
        messages, session, ctx, max_iters,
        gate_ltf_entry, accumulated_narratives,
        token_tracker=tracker,
    )
    accumulated_narratives.append(f"[STAGE 3 — LTF ENTRY]\n{text3}")
    if not cont:
        final = (
            f"CHAIN STOPPED at Stage 3 (LTF Entry) after retries exhausted.\n"
            f"Final gate reason: {gate3.reason}\n\n"
            f"Full chain so far:\n" + "\n\n".join(accumulated_narratives) + "\n\n"
            f"Decision: WATCH / NO_SETUP — no clean entry trigger with defined risk."
        )
        session.append("final_narrative", {"text": final, "stopped_at": "ltf_entry"})
        return final

    # ---------- Stage 4: Risk & Execution ----------
    # Pre-check confluence using raw Stage 3 text (gate needs structured fields)
    pre_gate = gate_confluence(text3 or "")

    base4 = (
        STAGE_PROMPTS["risk_exec"]
        + (f"\n\n--- Prior stage summary ---\n{brief}\n" if brief else "")
        + (f"\n\n[Full Stage 3 output for reference]\n{text3}" if text3 else "")
        + f"\n\nPre-check confluence result: {pre_gate.reason}"
    )
    if not pre_gate.passed:
        # HARD STOP: confl < 3 means no trade. Do not enter Stage 4.
        # This prevents the LLM from generating TRADE decisions on low-confluence setups.
        final = (
            "=== ICT CHAINED ANALYSIS COMPLETE ===\n\n"
            + "\n\n".join(accumulated_narratives)
            + f"\n\nPRE-CHECK FAILED: {pre_gate.reason}\n\n"
            "Decision: NO_SETUP — confluence bar not met. "
            "Per ICT discipline, standing aside is the correct response."
        )
        session.append("final_narrative", {"text": final, "stopped_at": "pre_gate_confluence"})
        session.append("chain_end", {"gates_passed": False, "stopped_at": "pre_gate_confluence",
                                      "reason": pre_gate.reason})
        return final

    text4, messages, gate4, _ = _run_stage_with_retries(
        kernel, adapter, system_prompt, "risk_exec", base4,
        messages, session, ctx, max_iters,
        gate_confluence, accumulated_narratives,
        token_tracker=tracker,
    )
    accumulated_narratives.append(f"[STAGE 4 — RISK & DECISION]\n{text4}")

    final = (
        "=== ICT CHAINED ANALYSIS COMPLETE ===\n\n"
        + "\n\n".join(accumulated_narratives)
    )
    session.append("final_narrative", {"text": final, "stopped_at": None})
    session.append("chain_end", {
        "gates_passed": True,
        "tokens": {
            "stage_used": tracker.stage_used(),
            "cycle_used": tracker.cycle_used(),
            "budget_per_stage": config.TOKEN_BUDGET_PER_STAGE,
            "budget_per_cycle": config.TOKEN_BUDGET_PER_CYCLE,
        },
    })
    return final
