"""
RUNTIME/ORCHESTRATION entry point.

Modes:
  - chained   (default)  → ICT staged analysis with gate checks + retries
  - free                 → original unrestricted ReAct loop
  - codegen              → outline → code → syntax-gate → refine
  - backtest             → run the from_video_2026_08_15 prompt set on historical data
  - forward              → run the forward_test prompt set for the coming / live week
"""
from __future__ import annotations
import re
import config
import os
MAX_STAGE_TIME = int(os.getenv("ICT_MAX_STAGE_TIME", "60"))
from instructions import SYSTEM_PROMPT
from harness.kernel import build_default_kernel
from harness.model_adapters import make_anthropic_adapter
from harness.node_llm_bridge import make_node_adapter
from harness.session_log import SessionLog
from harness.context import RunContext
from harness.loop import run as run_free_loop
from harness.chained_loop import run_chained
from harness.codegen_loop import run_codegen
from agent.prompt_loader import list_prompt_sets
from agent.prompt_set_runner import run_prompt_set_staged
from memory import store
from memory.session_state import get_session_state
from harness.observability import trace_chain, _get_client


def _build_adapter():
    """Select the best available LLM adapter."""
    # Always prefer native Anthropic SDK when we have a real key
    api_key = getattr(config, 'ANTHROPIC_API_KEY', '') or ''
    if len(api_key) > 20:
        try:
            adapter = make_anthropic_adapter(api_key, config.MODEL)
            # Quick health check
            result = adapter.call("Test", [], [{"role": "user", "content": "hi"}])
            if result.get('text', '').strip() or result.get('done'):
                print(f"[OK] Using native Anthropic adapter: {adapter.name}")
                return adapter
            else:
                print(f"[WARN] Native adapter returned empty, trying Node bridge")
        except Exception as e:
            print(f"[WARN] Anthropic adapter failed: {e}, falling back to Node bridge")
    # Fallback to Node.js bridge
    print(f"[FALLBACK] Using Node.js bridge")
    return make_node_adapter(provider="anthropic", model=config.MODEL)


def run_cycle(symbol: str, mode: str = "chained") -> str:
    """One full ICT analysis cycle for a symbol (chained or free)."""
    store.init_db()
    kernel = build_default_kernel()
    adapter = _build_adapter()
    session = SessionLog.start(symbol)
    ctx = RunContext()

    user_message = (
        f"Run a full ICT top-down analysis on {symbol}. "
        f"Higher timeframe = {config.HTF_INTERVAL}, entry timeframe = {config.LTF_INTERVAL}. "
        f"Follow the workflow in your instructions exactly. "
        f"Minimum reward:risk = {config.MIN_RR}. "
        f"Only place a trade if confluence bar is met; otherwise log a 'watch' "
        f"or 'no_setup' analysis and explain why."
    )

    # Extract key fields from narrative after run completes
    def _finalize_trace(narrative: str) -> None:
        try:
            import re
            dec_m = re.search(r"DECISION:\s*(TRADE|WATCH|NO_SETUP)", narrative, re.I)
            conf_m = re.search(r"CONFLUENCE_SCORE:\s*(\d)", narrative, re.I)
            dec = (dec_m.group(1).lower() if dec_m else "unknown")
            confluence = int(conf_m.group(1)) if conf_m else 0
            client = _get_client()
            client.score_current_trace(
                name="decision",
                value=1 if dec == "trade" else 0,
                comment=dec,
                metadata={"symbol": symbol, "confluence": confluence},
            )
        except Exception:
            pass  # non-critical

    with trace_chain(symbol, mode=mode):
        if mode == "free":
            narrative = run_free_loop(
                kernel, adapter, SYSTEM_PROMPT, user_message, session, ctx
            )
        else:
            narrative = run_chained(
                kernel, adapter, SYSTEM_PROMPT, user_message, session, ctx
            )

        # Persist cross-cycle state (bias + decision streak) for this symbol
        _update_session_state(symbol, narrative)
        # Finalize Langfuse trace with decision score
        _finalize_trace(narrative)

    print(f"[session: {session.path}]  [mode: {mode}]")
    return narrative


def _update_session_state(symbol: str, narrative: str) -> None:
    """Extract bias/decision from the chain narrative and persist to disk."""
    try:
        # Try structured DECISION line first
        dec_m = re.search(r"DECISION:\s*(TRADE|WATCH|NO_SETUP)", narrative, re.I)
        if not dec_m:
            # Fallback: look for patterns in the closing narrative
            n_lower = narrative.lower()
            if "place_paper_trade" in n_lower:
                dec = "trade"
            elif re.search(r"\bwatch\b", n_lower):
                dec = "watch"
            else:
                dec = "no_setup"
        else:
            dec = dec_m.group(1).lower()

        bias_m = re.search(r"BIAS:\s*(BULLISH|BEARISH|RANGING)", narrative, re.I)
        bias = (bias_m.group(1).upper() if bias_m else "UNKNOWN")

        state = get_session_state()
        state.update(symbol, bias=bias, decision=dec)
    except Exception as e:
        print(f"[WARN] session state update failed: {e}")


def run_codegen_task(task: str) -> str:
    adapter = _build_adapter()
    session = SessionLog.start("codegen")
    narrative = run_codegen(adapter, task, session)
    print(f"[session: {session.path}]  [mode: codegen]")
    return narrative


def run_prompt_set(
    set_name: str,
    symbol: str,
    week_label: str = "",
    extra_context: str = "",
) -> str:
    """
    Drive a full back-test or forward-test using one of the file-based
    prompt sets, as REAL per-stage gated calls (agent.prompt_set_runner) —
    not just a list of filenames handed to the generic 4-stage chain.

    set_name: "from_video_2026_08_15" | "forward_test" | any folder under prompts/
    symbol:   instrument to analyse (continuous contract preferred)
    week_label: e.g. "2026-08-04 to 2026-08-08" — the Monday date is parsed
                out to drive the Mon-Thu daily loop; falls back to generic
                day labels if it doesn't parse.
    extra_context: optional free-text every stage should see (calendar, notes, …)
    """
    store.init_db()
    kernel = build_default_kernel()
    adapter = _build_adapter()
    session = SessionLog.start(f"{symbol}_{set_name}")
    ctx = RunContext()

    week_start = None
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2})", week_label or "")
    if m:
        week_start = m.group(1)

    narrative = run_prompt_set_staged(
        set_name, symbol, kernel, adapter, session, ctx,
        week_start=week_start, extra_context=extra_context,
    )
    print(f"[session: {session.path}]  [mode: {set_name}]  [symbol: {symbol}]")
    return narrative
