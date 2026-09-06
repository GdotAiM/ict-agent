"""
Per-stage runner for file-based prompt sets (back-test + forward-test).

Unlike the generic 4-stage ICT analysis chain in harness/chained_loop.py,
this module drives the numbered stages defined under prompts/<set_name>/:

  00_weekend_prep → 01_weekly_levels → 02_draw_on_liquidity →
  03_15m_bellwether → 04_daily_process (Mon–Thu) → 05_tgif_friday →
  (optional) 06_multi_instrument

Each stage:
  - loads its system.md as the stage instruction
  - may call tools (broad allow-list for analysis tools)
  - is validated with gate_generic_required_fields (or a bespoke gate)
  - retries with feedback up to GATE_MAX_RETRIES
  - contributes locked facts to context for later stages
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Callable

import config
from agent.prompt_loader import load_prompt_set
from agent.gates import (
    GateResult,
    gate_generic_required_fields,
    gate_liquidity_sequencing,
    extract_required_fields,
    extract_generic_facts,
)
from harness.kernel import PluginKernel
from harness.plugin import ModelAdapterPlugin
from harness.context import RunContext
from harness.session_log import SessionLog
from instructions import SYSTEM_PROMPT

try:
    from memory.metrics import record_stage_metrics
except ImportError:
    def record_stage_metrics(*args, **kwargs):
        return []


# Stages that run once at the start of the week
WEEK_STAGES = [
    "00_weekend_prep",
    "01_weekly_levels",
    "02_draw_on_liquidity",
    "03_15m_bellwether",
]

# Daily stage (looped Mon–Thu when week_start is known)
DAILY_STAGE = "04_daily_process"

# Friday-only
FRIDAY_STAGE = "05_tgif_friday"

# Multi-instrument transposition (when symbol is not the native NQ set)
MULTI_STAGE = "06_multi_instrument"

# Tools allowed during prompt-set runs (analysis-focused; no execution by default)
PROMPT_SET_TOOLS = [
    "get_candles_summary",
    "get_market_structure",
    "get_liquidity_pools",
    "get_pd_array",
    "get_fair_value_gaps",
    "get_order_blocks",
    "get_kill_zone",
    "get_recent_context",
    "search_ict_knowledge",
    "log_analysis",
    "get_economic_calendar",
]


def _is_native_instrument(symbol: str) -> bool:
    native = getattr(config, "PROMPT_SET_NATIVE_INSTRUMENT", "NQ") or "NQ"
    return native.upper() in (symbol or "").upper()


def _weekdays_from_start(week_start: str | None) -> list[tuple[str, str]]:
    """
    Return [(label, iso_date), ...] for Mon–Thu of the week.
    If week_start is missing/unparseable, return generic day labels.
    """
    if not week_start:
        return [(d, "") for d in ("Monday", "Tuesday", "Wednesday", "Thursday")]
    try:
        start = datetime.strptime(week_start[:10], "%Y-%m-%d").date()
    except ValueError:
        return [(d, "") for d in ("Monday", "Tuesday", "Wednesday", "Thursday")]
    # Align to Monday of that week if needed
    start = start - timedelta(days=start.weekday())
    names = ["Monday", "Tuesday", "Wednesday", "Thursday"]
    return [(names[i], (start + timedelta(days=i)).isoformat()) for i in range(4)]


def _friday_from_start(week_start: str | None) -> tuple[str, str]:
    if not week_start:
        return ("Friday", "")
    try:
        start = datetime.strptime(week_start[:10], "%Y-%m-%d").date()
        start = start - timedelta(days=start.weekday())
        fri = start + timedelta(days=4)
        return ("Friday", fri.isoformat())
    except ValueError:
        return ("Friday", "")


def _filter_tools(kernel: PluginKernel, allowed: list[str]) -> list[dict]:
    allowed_set = set(allowed)
    return [s for s in kernel.tool_schemas() if s.get("name") in allowed_set]


def _gate_for_stage(stage_name: str, stage_prompt: str) -> Callable[[str], GateResult]:
    """Return a gate function appropriate for this stage file."""
    # Bespoke gate for the liquidity-sequencing style prompt
    if "02_draw_on_liquidity" in stage_name:
        # Prefer bespoke if the prompt looks like the sequencing engine
        if "FIRST_LIQUIDITY_EVENT" in stage_prompt or "HTF_DIRECTIONAL_BIAS" in stage_prompt:
            return lambda narrative: gate_liquidity_sequencing(narrative)

    required = extract_required_fields(stage_prompt)

    def _gate(narrative: str) -> GateResult:
        return gate_generic_required_fields(narrative, required)

    return _gate


def _run_one_stage(
    *,
    kernel: PluginKernel,
    adapter: ModelAdapterPlugin,
    system_prompt: str,
    stage_name: str,
    stage_instruction: str,
    user_payload: str,
    session: SessionLog,
    ctx: RunContext,
    symbol: str,
    mode: str,
    week_label: str,
    max_iters: int,
) -> tuple[str, GateResult]:
    """
    Run a single stage with tool calls + gate retries. Each stage gets its
    OWN fresh message list — it does not see prior stages' raw conversation,
    only the compact locked_facts summary baked into user_payload. Carrying
    the full transcript of every earlier stage into every later call was
    exactly the "wall of prose" clash risk this runner was built to avoid
    (see module docstring / run_prompt_set_staged's locked-facts mechanism)
    — the two aren't meant to coexist.
    Returns (final_narrative, final_gate).
    """
    gate_fn = _gate_for_stage(stage_name, stage_instruction)
    allowed = PROMPT_SET_TOOLS
    tools = _filter_tools(kernel, allowed)
    max_retries = getattr(config, "GATE_MAX_RETRIES", 2)

    # Combined system: global ICT identity + this stage's file prompt
    combined_system = (
        system_prompt
        + "\n\n=== STAGE INSTRUCTION (from prompt set) ===\n"
        + stage_instruction
    )

    stage_text = ""
    gate = GateResult(passed=False, reason="not run")
    attempt = 0
    messages: list = []  # fresh per stage — see docstring

    while attempt <= max_retries:
        session.append("stage_start", {
            "stage": stage_name,
            "attempt": attempt,
            "allowed_tools": allowed,
        })

        prompt_body = user_payload
        if attempt > 0 and gate.feedback:
            prompt_body = (
                user_payload
                + "\n\n=== GATE CHECK FAILED (attempt "
                + f"{attempt}/{max_retries}) ===\n"
                + gate.feedback
                + "\n\nRe-do this stage carefully. Emit every required field."
            )
            session.append("gate_retry", {
                "stage": stage_name,
                "attempt": attempt,
                "reason": gate.reason,
            })

        messages.append({"role": "user", "content": prompt_body})

        stage_text = ""
        for step in range(max_iters):
            response = adapter.call(combined_system, tools, messages)
            messages.append(adapter.to_assistant_message(response))
            text = adapter.extract_text(response)
            calls = adapter.extract_tool_calls(response)
            session.append("model_response", {
                "stage": stage_name,
                "step": step,
                "attempt": attempt,
                "text": text,
                "tool_calls": [c["name"] for c in calls],
            })
            if text:
                stage_text = text
            if adapter.is_done(response):
                break
            results = []
            for call in calls:
                if call["name"] not in allowed:
                    result = {"error": f"tool '{call['name']}' not permitted in prompt-set stages"}
                else:
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
            messages.append(adapter.to_tool_result_message(results))

        gate = gate_fn(stage_text)
        session.append("gate_check", {
            "stage": stage_name,
            "attempt": attempt,
            "passed": gate.passed,
            "reason": gate.reason,
            "extracted": gate.extracted,
        })
        try:
            record_stage_metrics(
                session, symbol=symbol, mode=mode, stage=stage_name,
                narrative=stage_text, gate_passed=gate.passed,
                gate_reason=gate.reason, week_label=week_label, retries=attempt,
            )
        except Exception:
            pass

        session.append("stage_end", {
            "stage": stage_name,
            "attempt": attempt,
            "narrative": stage_text,
            "passed": gate.passed,
        })

        if gate.passed:
            break
        attempt += 1

    return stage_text, gate


def _facts_block(locked: dict) -> str:
    if not locked:
        return "(none yet)"
    lines = [f"{k}: {v}" for k, v in locked.items()]
    return "\n".join(lines)


def run_prompt_set_staged(
    set_name: str,
    symbol: str,
    kernel: PluginKernel,
    adapter: ModelAdapterPlugin,
    session: SessionLog,
    ctx: RunContext,
    week_start: str | None = None,
    extra_context: str = "",
) -> str:
    """
    Full back-test or forward-test execution over a prompt set directory.
    """
    stages = load_prompt_set(set_name)
    mode = set_name
    week_label = week_start or ""
    max_iters = max(5, getattr(config, "MAX_TOOL_ITERATIONS", 6))

    session.append("chain_start", {
        "mode": "prompt_set",
        "set_name": set_name,
        "symbol": symbol,
        "week_start": week_start,
        "stages_present": list(stages.keys()),
    })
    session.append("system_prompt", {"text": SYSTEM_PROMPT[:500] + "…"})

    locked_facts: dict = {}
    narratives: list[str] = []
    hard_stop = getattr(config, "GATE_HARD_STOP_ON_EXHAUST", True)

    def run_stage(stage_name: str, extra_user: str = "") -> bool:
        nonlocal locked_facts
        if stage_name not in stages:
            return True
        calendar_hint = ""
        if "02_draw_on_liquidity" in stage_name or "00_weekend" in stage_name:
            calendar_hint = (
                "Call get_economic_calendar for the week (or state KEY_EVENTS: UNKNOWN). "
                "High-impact releases time profile delivery — do not invent events.\n"
            )
        user_payload = (
            f"Instrument: {symbol}\n"
            f"Week: {week_label or '(unspecified)'}\n"
            f"Stage: {stage_name}\n{calendar_hint}\n"
            f"--- Locked facts from prior stages ---\n{_facts_block(locked_facts)}\n\n"
        )
        if extra_context:
            user_payload += f"--- Extra context ---\n{extra_context}\n\n"
        if extra_user:
            user_payload += extra_user + "\n\n"
        user_payload += (
            "Follow the STAGE INSTRUCTION exactly. "
            "Use tools as needed. End with the Required Output structured block."
        )

        text, gate = _run_one_stage(
            kernel=kernel,
            adapter=adapter,
            system_prompt=SYSTEM_PROMPT,
            stage_name=stage_name,
            stage_instruction=stages[stage_name],
            user_payload=user_payload,
            session=session,
            ctx=ctx,
            symbol=symbol,
            mode=mode,
            week_label=week_label,
            max_iters=max_iters,
        )
        narratives.append(f"[{stage_name}]\n{text}")

        # Merge extracted facts into locked context
        req = extract_required_fields(stages[stage_name])
        facts = extract_generic_facts(text, req) if req else {}
        if gate.extracted.get("facts"):
            facts.update(gate.extracted["facts"])
        if gate.extracted.get("sequencing"):
            for k, v in gate.extracted["sequencing"].items():
                if v:
                    facts[k.upper() if isinstance(k, str) else k] = v
        locked_facts.update(facts)

        if not gate.passed and hard_stop and not gate.soft:
            narratives.append(
                f"[STOP] Stage {stage_name} failed after retries: {gate.reason}"
            )
            return False
        return True

    # Optional multi-instrument first when symbol is not native NQ set
    if MULTI_STAGE in stages and not _is_native_instrument(symbol):
        if not run_stage(MULTI_STAGE, extra_user="Map continuous-contract logic onto this executable symbol."):
            final = "\n\n".join(narratives)
            session.append("final_narrative", {"text": final, "stopped_at": MULTI_STAGE})
            return final

    # Week-level stages
    for stage_name in WEEK_STAGES:
        if not run_stage(stage_name):
            final = "\n\n".join(narratives)
            session.append("final_narrative", {"text": final, "stopped_at": stage_name})
            return final

    # Daily loop Mon–Thu
    if DAILY_STAGE in stages:
        for day_name, day_iso in _weekdays_from_start(week_start):
            extra = (
                f"DATE: {day_iso or day_name}\n"
                f"Day of week: {day_name}\n"
                f"Call get_economic_calendar for this DATE before locking DAILY_BIAS.\n"
                f"Emit KEY_EVENTS_TODAY and DELIVERY_NOTE.\n"
                f"If a high-impact event is within ~90 minutes, prefer WATCH until after "
                f"the print and 15m displacement.\n"
                f"Form today's Daily Bias only after the calendar check."
            )
            if not run_stage(DAILY_STAGE, extra_user=extra):
                final = "\n\n".join(narratives)
                session.append("final_narrative", {"text": final, "stopped_at": f"{DAILY_STAGE}:{day_name}"})
                return final

    # Friday TGIF
    if FRIDAY_STAGE in stages:
        day_name, day_iso = _friday_from_start(week_start)
        extra = f"DATE: {day_iso or day_name}\nDay of week: {day_name}\nEvaluate TGIF behaviour for this week."
        if not run_stage(FRIDAY_STAGE, extra_user=extra):
            final = "\n\n".join(narratives)
            session.append("final_narrative", {"text": final, "stopped_at": FRIDAY_STAGE})
            return final

    final = (
        f"=== PROMPT SET COMPLETE ({set_name}) ===\n"
        f"Symbol: {symbol}\nWeek: {week_label or 'n/a'}\n\n"
        + "\n\n".join(narratives)
    )
    session.append("final_narrative", {"text": final, "stopped_at": None})
    session.append("chain_end", {"mode": "prompt_set", "set_name": set_name, "success": True})
    return final
