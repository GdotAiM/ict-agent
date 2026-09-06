"""
Phase A — Feedback-loop requirements gatherer.

Collects a RUN_SPEC via multi-turn conversation (one missing field at a time)
before any analysis chain is allowed to start.

Works offline with a deterministic field extractor so the desk can brief
without an API key. The same checklist is embedded in
prompts/feedback_loop/requirements_gatherer/system.md for Bedrock / LLM use.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

PROMPTS_ROOT = Path(__file__).resolve().parent.parent / "prompts"
BRIEF_PROMPT_PATH = PROMPTS_ROOT / "feedback_loop" / "requirements_gatherer" / "system.md"

REQUIRED = [
    "INSTRUMENT",
    "MODE",
    "WEEK_LABEL",
    "RISK_PCT",
    "SESSION_FOCUS",
    "NEWS_POLICY",
]
OPTIONAL = ["ACCOUNT_TYPE", "NOTES"]

MODE_ALIASES = {
    # order matters only via explicit search below (longest/clearest first)
    "trade journal": "journal",
    "back-test": "backtest",
    "backtest": "backtest",
    "historical": "backtest",
    "forward": "forward",
    "live": "forward",
    "fwd": "forward",
    "journal": "journal",
    "chained": "chained",
    "chain": "chained",
    "bt": "backtest",
}

SESSION_ALIASES = {
    "london": "London",
    "ny": "NY_AM",
    "ny_am": "NY_AM",
    "new york": "NY_AM",
    "ny am": "NY_AM",
    "both": "both",
    "all": "both",
    "none": "none",
}

NEWS_ALIASES = {
    "flatten": "flatten_before_high_impact",
    "flatten_before_high_impact": "flatten_before_high_impact",
    "flatten before": "flatten_before_high_impact",
    "trade through": "trade_through",
    "trade_through": "trade_through",
    # NOTE: bare "watch" deliberately excluded — too common a standalone
    # word ("I'll watch this trade") to safely trigger a policy even with
    # word-boundary matching. Only the specific multi-word/underscore forms
    # below count as an intentional choice of this policy.
    "watch_only_into_news": "watch_only_into_news",
    "watch only": "watch_only_into_news",
}

INSTRUMENT_HINTS = {
    r"\bnq\b|\bnas100\b|\bnasdaq\b|\bmnq\b": "NQ=F",
    r"\bes\b|\bs&p\b|\bspx\b|\bmes\b": "ES=F",
    r"\bgold\b|\bxau\b|\bgc=f\b|\bxauusd\b": "GC=F",
    r"\beurusd\b|\beuro\b": "EURUSD=X",
    r"\bgbpusd\b|\bcable\b|\bpound\b": "GBPUSD=X",
    r"\busdjpy\b|\byen\b": "USDJPY=X",
}


@dataclass
class RunSpec:
    INSTRUMENT: Optional[str] = None
    MODE: Optional[str] = None
    WEEK_LABEL: Optional[str] = None
    RISK_PCT: Optional[float] = None
    SESSION_FOCUS: Optional[str] = None
    NEWS_POLICY: Optional[str] = None
    ACCOUNT_TYPE: Optional[str] = "paper"
    NOTES: Optional[str] = None

    def missing_required(self) -> list[str]:
        missing = []
        for k in REQUIRED:
            val = getattr(self, k)
            if val is None or val == "":
                missing.append(k)
            # WEEK_LABEL only strictly required for backtest
            if k == "WEEK_LABEL" and self.MODE and self.MODE != "backtest":
                if val is None:
                    setattr(self, "WEEK_LABEL", "n/a")
                if k in missing:
                    missing.remove(k)
        return missing

    def is_complete(self) -> bool:
        return len(self.missing_required()) == 0

    def to_block(self) -> str:
        return (
            "RUN_SPEC\n"
            f"INSTRUMENT: {self.INSTRUMENT}\n"
            f"MODE: {self.MODE}\n"
            f"WEEK_LABEL: {self.WEEK_LABEL}\n"
            f"RISK_PCT: {self.RISK_PCT}\n"
            f"SESSION_FOCUS: {self.SESSION_FOCUS}\n"
            f"NEWS_POLICY: {self.NEWS_POLICY}\n"
            f"ACCOUNT_TYPE: {self.ACCOUNT_TYPE or 'paper'}\n"
            f"NOTES: {self.NOTES or 'none'}\n"
            "CHECKLIST_COMPLETE: YES\n"
        )

    def summary_have(self) -> str:
        parts = []
        for k in REQUIRED + OPTIONAL:
            v = getattr(self, k)
            if v is not None and v != "":
                parts.append(f"{k}={v}")
        return ", ".join(parts) if parts else "(nothing locked yet)"


QUESTIONS = {
    "INSTRUMENT": (
        "Which **INSTRUMENT** should we run? "
        "(e.g. NQ=F, GC=F / XAUUSD, EURUSD=X, GBPUSD=X)"
    ),
    "MODE": (
        "What **MODE**? "
        "`forward` (live week), `backtest` (historical week), `chained` (single-cycle analysis), or `journal`."
    ),
    "WEEK_LABEL": (
        "What **WEEK_LABEL** for the back-test? "
        "Use dates like `2026-08-02 to 2026-08-08` (Monday start preferred)."
    ),
    "RISK_PCT": (
        "What **RISK_PCT** per idea? "
        "(e.g. `0.5` for half a percent of equity — or say `default` for 0.5)"
    ),
    "SESSION_FOCUS": (
        "What **SESSION_FOCUS**? "
        "`London`, `NY_AM`, `both`, or `none` — or `default` for both."
    ),
    "NEWS_POLICY": (
        "What **NEWS_POLICY** into high-impact releases? "
        "`flatten_before_high_impact`, `trade_through`, or `watch_only_into_news` "
        "— or `default` for flatten_before_high_impact."
    ),
}


def _extract_into(spec: RunSpec, text: str) -> None:
    t = text.strip()
    low = t.lower()

    # defaults if user says so
    if re.search(r"\b(default|defaults|you choose|whatever)\b", low):
        if spec.RISK_PCT is None:
            spec.RISK_PCT = 0.5
        if spec.SESSION_FOCUS is None:
            spec.SESSION_FOCUS = "both"
        if spec.NEWS_POLICY is None:
            spec.NEWS_POLICY = "flatten_before_high_impact"
        if spec.MODE and spec.MODE != "backtest" and not spec.WEEK_LABEL:
            spec.WEEK_LABEL = "n/a"

    # MODE — explicit keywords only (do not treat "analyse the market" as MODE)
    if spec.MODE is None:
        for key, norm in MODE_ALIASES.items():
            if re.search(rf"\b{re.escape(key)}\b", low):
                spec.MODE = norm
                break

    # INSTRUMENT — explicit ticker first
    if spec.INSTRUMENT is None:
        m = re.search(
            r"\b([A-Z]{1,6}=F|[A-Z]{6}=X|[A-Z]{3}USD(?:\=X)?|XAUUSD|XAGUSD|MNQ|MES|NQ|ES|GC)\b",
            t,
            re.I,
        )
        if m:
            raw = m.group(1).upper()
            # normalize shorts
            mapping = {
                "NQ": "NQ=F", "MNQ": "MNQ=F", "ES": "ES=F", "MES": "MES=F",
                "GC": "GC=F", "XAUUSD": "GC=F", "EURUSD": "EURUSD=X",
                "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
            }
            spec.INSTRUMENT = mapping.get(raw, raw if "=" in raw else mapping.get(raw, raw))
        else:
            for pat, sym in INSTRUMENT_HINTS.items():
                if re.search(pat, low):
                    spec.INSTRUMENT = sym
                    break

    # WEEK_LABEL — date range
    if spec.WEEK_LABEL is None:
        m = re.search(
            r"(20\d{2}-\d{2}-\d{2})\s*(?:to|–|-)\s*(20\d{2}-\d{2}-\d{2})",
            t,
        )
        if m:
            spec.WEEK_LABEL = f"{m.group(1)} to {m.group(2)}"
        elif spec.MODE == "forward" or (spec.MODE and spec.MODE != "backtest"):
            if re.search(r"\b(this week|current week|live)\b", low):
                spec.WEEK_LABEL = "n/a"

    # RISK_PCT
    if spec.RISK_PCT is None:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", t)
        if m:
            spec.RISK_PCT = float(m.group(1))
        else:
            m = re.search(r"risk(?:_pct)?\s*[:=]?\s*(\d+(?:\.\d+)?)", low)
            if m:
                spec.RISK_PCT = float(m.group(1))

    # SESSION — word-boundary match only (substring "in" would false-positive
    # on ordinary words like "any"/"many" containing "ny", "call"/"tall"
    # containing "all", etc.)
    if spec.SESSION_FOCUS is None:
        for key, norm in SESSION_ALIASES.items():
            if re.search(rf"\b{re.escape(key)}\b", low):
                spec.SESSION_FOCUS = norm
                break

    # NEWS — same word-boundary reasoning ("watch" as a stray verb, e.g.
    # "I'll watch this trade", shouldn't lock in a news policy)
    if spec.NEWS_POLICY is None:
        for key, norm in NEWS_ALIASES.items():
            if re.search(rf"\b{re.escape(key)}\b", low):
                spec.NEWS_POLICY = norm
                break

    # ACCOUNT
    if re.search(r"\bfutures?\b", low):
        spec.ACCOUNT_TYPE = "futures"
    elif re.search(r"\bcfd\b", low):
        spec.ACCOUNT_TYPE = "CFD"
    elif re.search(r"\bspot\b", low):
        spec.ACCOUNT_TYPE = "spot"
    elif re.search(r"\bpaper\b", low):
        spec.ACCOUNT_TYPE = "paper"

    # NOTES — keep residual short phrases if user said "note:"
    m = re.search(r"notes?\s*:\s*(.+)$", t, re.I)
    if m:
        spec.NOTES = m.group(1).strip()


def next_question(spec: RunSpec) -> str:
    missing = spec.missing_required()
    if not missing:
        return ""
    # priority order = REQUIRED list order
    field = missing[0]
    return QUESTIONS[field]


def process_turn(spec: RunSpec, user_text: str) -> tuple[str, bool]:
    """
    Apply user_text to spec. Returns (assistant_message, complete).
    """
    _extract_into(spec, user_text)
    if spec.is_complete():
        return spec.to_block(), True
    have = spec.summary_have()
    q = next_question(spec)
    msg = f"Locked so far: {have}\n\n{q}"
    return msg, False


def load_brief_system_prompt() -> str:
    if BRIEF_PROMPT_PATH.is_file():
        return BRIEF_PROMPT_PATH.read_text(encoding="utf-8")
    return "Collect INSTRUMENT, MODE, WEEK_LABEL, RISK_PCT, SESSION_FOCUS, NEWS_POLICY."


def run_brief_interactive() -> Optional[RunSpec]:
    """
    CLI multi-turn loop. Returns completed RunSpec or None if aborted.
    """
    print("=" * 60)
    print("ICT DESK — Requirements gatherer (feedback loop)")
    print("Type your request. One question at a time until RUN_SPEC is complete.")
    print("Commands:  quit | show | prompt")
    print("=" * 60)

    spec = RunSpec()
    # Seed with empty turn so we always open with first question if user
    # starts with a full sentence on first input.
    first = input("\nYou: ").strip()
    if first.lower() in ("quit", "exit", "q"):
        return None
    if first.lower() == "prompt":
        print(load_brief_system_prompt()[:1500])
        first = input("\nYou: ").strip()

    while True:
        if first.lower() in ("quit", "exit", "q"):
            print("Aborted. No RUN_SPEC.")
            return None
        if first.lower() == "show":
            print(spec.summary_have())
            first = input("\nYou: ").strip()
            continue

        reply, done = process_turn(spec, first)
        print(f"\nDesk: {reply}")
        if done:
            print("\nChecklist complete. Analysis chains may now use this RUN_SPEC.")
            return spec
        first = input("\nYou: ").strip()


def parse_run_spec_block(text: str) -> Optional[RunSpec]:
    """Parse a RUN_SPEC block from text (e.g. pasted or LLM-emitted)."""
    if "RUN_SPEC" not in text and "CHECKLIST_COMPLETE" not in text:
        return None
    spec = RunSpec()

    def grab(key: str) -> Optional[str]:
        m = re.search(rf"{key}\s*:\s*(.+)", text, re.I)
        return m.group(1).strip() if m else None

    inst = grab("INSTRUMENT")
    mode = grab("MODE")
    week = grab("WEEK_LABEL")
    risk = grab("RISK_PCT")
    sess = grab("SESSION_FOCUS")
    news = grab("NEWS_POLICY")
    acct = grab("ACCOUNT_TYPE")
    notes = grab("NOTES")
    if inst:
        spec.INSTRUMENT = inst
    if mode:
        spec.MODE = mode.lower()
    if week:
        spec.WEEK_LABEL = week
    if risk:
        try:
            spec.RISK_PCT = float(re.search(r"[\d.]+", risk).group())
        except Exception:
            pass
    if sess:
        spec.SESSION_FOCUS = sess
    if news:
        spec.NEWS_POLICY = news
    if acct:
        spec.ACCOUNT_TYPE = acct
    if notes and notes.lower() != "none":
        spec.NOTES = notes
    return spec if spec.is_complete() else None
