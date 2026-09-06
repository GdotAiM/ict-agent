"""
Thin loader for the timestamp-grounded prompt sets.

Usage from runtime / main:
    from agent.prompt_loader import load_prompt_set, list_prompt_sets

    stages = load_prompt_set("forward_test")          # or "from_video_2026_08_15"
    weekend = stages["00_weekend_prep"]               # full system prompt text
"""
from __future__ import annotations
from pathlib import Path

PROMPTS_ROOT = Path(__file__).resolve().parent.parent / "prompts"

# Canonical stage order for both back-test and forward-test sets
STAGE_ORDER = [
    "00_weekend_prep",
    "01_weekly_levels",
    "02_draw_on_liquidity",
    "03_15m_bellwether",
    "04_daily_process",
    "05_tgif_friday",
    "06_multi_instrument",
    "07_backtest_runner",   # only present in back-test set
    "07_forward_runner",    # only present in forward-test set
]


def list_prompt_sets() -> list[str]:
    if not PROMPTS_ROOT.exists():
        return []
    return sorted(
        p.name for p in PROMPTS_ROOT.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def load_prompt_set(name: str) -> dict[str, str]:
    """
    Returns {stage_name: system_prompt_text} for the requested set.
    Missing stages are simply omitted.
    """
    root = PROMPTS_ROOT / name
    if not root.is_dir():
        raise FileNotFoundError(
            f"Prompt set '{name}' not found under {PROMPTS_ROOT}. "
            f"Available: {list_prompt_sets()}"
        )

    stages: dict[str, str] = {}
    for stage in STAGE_ORDER:
        path = root / stage / "system.md"
        if path.is_file():
            stages[stage] = path.read_text(encoding="utf-8")
    if not stages:
        raise FileNotFoundError(f"No system.md files found inside {root}")
    return stages


def get_runner_prompt(name: str) -> str:
    """Convenience: return the orchestrator prompt for the set."""
    stages = load_prompt_set(name)
    for key in ("07_forward_runner", "07_backtest_runner"):
        if key in stages:
            return stages[key]
    raise KeyError(f"No runner prompt found in set '{name}'")
