"""
Usage:
    python main.py                       run one cycle (chained) across the watchlist
    python main.py SPY                   single symbol, chained
    python main.py --free SPY            free-form ReAct
    python main.py --chained SPY         explicit chained

    python main.py codegen "task text"   outline → code → syntax-gate → refine

    python main.py backtest SYMBOL [--week "YYYY-MM-DD to YYYY-MM-DD"]
        Run the from_video_2026_08_15 prompt set on historical data for grounding checks.

    python main.py forward SYMBOL [--week "YYYY-MM-DD to YYYY-MM-DD"]
        Run the forward_test prompt set for the coming / live week.

    python main.py prompts               list available prompt sets

    python main.py brief                feedback-loop requirements gatherer → RUN_SPEC

    python main.py metrics <session_id>  summarise gate/decision metrics for a session
    python main.py metrics export        dump all metrics to CSV

    python main.py sessions
    python main.py replay <session.jsonl>
    python main.py fork <session.jsonl> <step_index>
"""
import sys
import os
import json
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# Fix SSL certificate verification on Windows
# The certifi bundle fails to load in Python 3.14 due to strict PEM parsing changes.
# Clear any env vars pointing to the broken bundle so httpx falls back to the
# system cert store (or the Avast MIT cert via NODE_EXTRA_CA_CERTS).
import os as _os
for _k in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'):
    _os.environ.pop(_k, None)

def _patch_ssl():
    """Patch all HTTP client libraries to work around the broken certifi bundle."""
    import ssl
    # 1) Override urllib default context (patches requests, urllib3 too)
    ssl._create_default_https_context = ssl._create_unverified_context
    # 2) Patch httpx — it reads SSL_CERT_FILE before creating its context
    try:
        import httpx
        _orig_create = httpx._config.create_ssl_context
        def _fixed_create_ssl_context(verify=True, cert=None, trust_env=True):
            if isinstance(verify, bool) and verify:
                # Use a context that accepts any cert (Avast MITM + broken bundle)
                return ssl._create_unverified_context()
            return _orig_create(verify=verify, cert=cert, trust_env=trust_env)
        httpx._config.create_ssl_context = _fixed_create_ssl_context
    except Exception:
        pass
    # 3) Patch httpcore (底层 transport)
    try:
        import httpcore
        _orig_httpcore = getattr(httpcore, '_ssl', None)
        if _orig_httpcore:
            _orig_ctx = getattr(_orig_httpcore, 'create_ssl_context', None)
            if _orig_ctx:
                def _fixed_httpcore_ssl(*a, **kw):
                    return ssl._create_unverified_context()
                _orig_httpcore.create_ssl_context = _fixed_httpcore_ssl
    except Exception:
        pass

_patch_ssl()
import config
from agent.runtime import run_cycle, run_codegen_task, run_prompt_set
from agent.prompt_loader import list_prompt_sets
from harness.session_log import SessionLog
from memory.metrics import summarise_session, export_metrics_csv, init_metrics_db
from agent.brief import run_brief_interactive, RunSpec

USAGE = """
Usage: python main.py <command> [args]

Commands:
  [SYMBOL | --free SYMBOL | --chained SYMBOL]   run ICT analysis chain
      No args           -> runs chained analysis over the full watchlist
      python main.py SPY            -> single symbol, chained
      python main.py --free SPY     -> free-form ReAct loop
      python main.py --chained SPY  -> explicit chained (same as default)

  codegen "task"       outline -> code -> syntax-gate -> refine
  backtest SYMBOL [--week "label"]   historical prompt-set run
  forward SYMBOL [--week "label"]    forward-looking prompt-set run
  prompts                  list available prompt sets under prompts/
  brief                    interactive requirements gatherer -> RUN_SPEC
  metrics [session_id | export]  show session metrics or dump CSV
  sessions                 list all saved session logs
  replay <session.jsonl>   print a session log to stdout
  fork <session.jsonl> <step>  copy first N events into a new session file

Options:
  -h, --help               show this help text and exit
"""


def cmd_help():
    print(USAGE.strip())
    sys.exit(0)


def cmd_run(symbols, mode: str = "chained"):
    symbols = symbols or config.WATCHLIST
    for symbol in symbols:
        symbol = symbol.strip()
        if not symbol or symbol.startswith("--"):
            continue
        print(f"\n{'=' * 60}\n{symbol}  [{mode}]\n{'=' * 60}")
        try:
            print(run_cycle(symbol, mode=mode))
        except Exception as e:
            print(f"[error] {symbol}: {e}")


def cmd_codegen(task: str):
    if not task.strip():
        print("Usage: python main.py codegen \"your task description\"")
        return
    print(f"\n{'=' * 60}\nCODEGEN\n{'=' * 60}")
    try:
        print(run_codegen_task(task))
    except Exception as e:
        print(f"[error] codegen: {e}")


def cmd_prompt_set(kind: str, args: list[str]):
    """
    kind = "backtest" | "forward"
    args = [SYMBOL, optional --week "label", optional extra flags]
    """
    if not args:
        print(f"Usage: python main.py {kind} SYMBOL [--week \"label\"]")
        return
    symbol = args[0]
    week = ""
    if "--week" in args:
        idx = args.index("--week")
        if idx + 1 < len(args):
            week = args[idx + 1]

    set_name = (
        "from_video_2026_08_15" if kind == "backtest" else "forward_test"
    )
    print(f"\n{'=' * 60}\n{kind.upper()}  {symbol}  [{set_name}]\n{'=' * 60}")
    try:
        print(run_prompt_set(set_name, symbol, week_label=week))
    except Exception as e:
        print(f"[error] {kind}: {e}")


def cmd_prompts():
    sets = list_prompt_sets()
    if not sets:
        print("No prompt sets found under prompts/")
        return
    print("Available prompt sets:")
    for s in sets:
        print(f"  - {s}")


def cmd_sessions():
    for name in SessionLog.list_sessions():
        print(name)


def cmd_replay(path):
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join("sessions", path)
    if not os.path.exists(path):
        print(f"[error] session file not found: {path}")
        print(f"Available sessions:")
        for name in SessionLog.list_sessions():
            print(f"  - {name}")
        sys.exit(2)
    try:
        for i, event in enumerate(SessionLog.replay(path)):
            print(f"[{i}] {event['ts']}  {event['type']}")
            if event["type"] in (
                "tool_call", "tool_result", "final_narrative", "user_message",
                "gate_check", "stage_start", "stage_end", "codegen_prompt",
                "codegen_response", "codegen_result",
            ):
                print(f"    {event['data']}")
    except json.JSONDecodeError as e:
        print(f"[error] corrupted session file at line {e.lineno}: {e.msg}")
        sys.exit(2)


def cmd_fork(path, step_index):
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join("sessions", path)
    if not os.path.exists(path):
        print(f"[error] session file not found: {path}")
        print(f"Available sessions:")
        for name in SessionLog.list_sessions():
            print(f"  - {name}")
        sys.exit(2)
    try:
        idx = int(step_index)
    except ValueError:
        print(f"[error] step index must be an integer, got: {step_index!r}")
        sys.exit(2)
    new_path = SessionLog.fork(path, idx)
    print(f"forked -> {new_path}")



def cmd_metrics(args):
    """python main.py metrics [session_id]  OR  python main.py metrics export"""
    init_metrics_db()
    if not args:
        print("Usage:")
        print("  python main.py metrics <session_id>   # summarise one session")
        print("  python main.py metrics export         # dump CSV")
        return
    if args[0] == "export":
        path = export_metrics_csv(args[1] if len(args) > 1 else "metrics_export.csv")
        print(f"exported -> {path}")
        return
    summary = summarise_session(args[0])
    print(f"Session : {summary['session_id']}")
    print(f"Gates   : {summary['gates_passed']} passed / {summary['gates_failed']} failed")
    print(f"Retries : {summary['total_retries']}")
    print(f"Decisions: {summary['decisions']}")
    print(f"Fields  : {summary['fields_seen']}")
    print(f"Confluence scores: {summary['confluence_scores']}")



def main():
    args = sys.argv[1:]
    mode = "chained"
    if "--free" in args:
        mode = "free"
        args = [a for a in args if a != "--free"]
    if "--chained" in args:
        mode = "chained"
        args = [a for a in args if a != "--chained"]

    # Flag handling (only when flags are explicitly passed)
    if ("-h" in args or "--help" in args):
        cmd_help()

    head = args[0] if args else ""
    if head == "codegen":
        cmd_codegen(" ".join(args[1:]))
    elif head == "backtest":
        cmd_prompt_set("backtest", args[1:])
    elif head == "forward":
        cmd_prompt_set("forward", args[1:])
    elif head == "brief":
        try:
            cmd_brief()
        except EOFError:
            print("\n[interrupted] brief aborted (no tty available).")
            sys.exit(0)
    elif head == "prompts":
        cmd_prompts()
    elif head == "metrics":
        cmd_metrics(args[1:])
    elif head == "sessions":
        cmd_sessions()
    elif head == "replay":
        if len(args) < 2:
            print('Usage: python main.py replay <session.jsonl>')
            print('Available sessions:')
            for name in SessionLog.list_sessions():
                print(f"  - {name}")
            sys.exit(2)
        cmd_replay(args[1])
    elif head == "fork":
        if len(args) < 3:
            print('Usage: python main.py fork <session.jsonl> <step_index>')
            sys.exit(2)
        cmd_fork(args[1], args[2])
    else:
        cmd_run(args, mode=mode)



def cmd_brief():
    """Multi-turn requirements gatherer → RUN_SPEC (Phase A feedback loop)."""
    try:
        spec = run_brief_interactive()
    except EOFError:
        print("\n[interrupted] brief aborted (no tty available).")
        return
    if spec is None:
        return
    print("\n" + "=" * 60)
    print(spec.to_block())
    # Optional hand-off
    try:
        ans = input("Launch analysis with this RUN_SPEC now? [y/N]: ").strip().lower()
    except EOFError:
        ans = "n"
    if ans != "y":
        print("RUN_SPEC ready. Re-run later with the printed fields.")
        return
    sym = spec.INSTRUMENT
    week = spec.WEEK_LABEL or ""
    if week == "n/a":
        week = ""
    if spec.MODE == "backtest":
        cmd_prompt_set("backtest", [sym, "--week", week] if week else [sym])
    elif spec.MODE == "forward":
        cmd_prompt_set("forward", [sym, "--week", week] if week else [sym])
    elif spec.MODE == "journal":
        print("Journal mode: use sessions/ and trade journal markdown; no auto chain.")
        print(f"Suggested focus: {sym} | risk {spec.RISK_PCT}% | news: {spec.NEWS_POLICY}")
    else:
        cmd_run([sym], mode="chained")


if __name__ == "__main__":
    main()
