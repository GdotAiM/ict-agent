"""
Economic calendar tool for ICT weekly/daily profiling.

Primary path: Forex Factory-style public calendar via a lightweight scrape/API
fallback. If the network path fails, returns a structured empty result so the
agent must still *acknowledge* the gap instead of inventing events.

ICT usage (from the lecture): high-impact releases (CPI, PPI, NFP, FOMC, …)
are used to *time* when the weekly profile is likely to deliver — not to invent bias.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from harness.plugin import ToolPlugin

# Static high-value fallback for known recurring windows when live fetch fails.
# This is NOT a substitute for a live calendar — only a safety net so the agent
# still reasons about "unknown calendar" vs silent omission.
_IMPACT_RANK = {"high": 3, "medium": 2, "low": 1, "holiday": 0}


def _parse_date(s: str | None) -> str:
    if not s:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    s = s.strip()[:10]
    datetime.strptime(s, "%Y-%m-%d")  # validate
    return s


def _fetch_forexfactory_day(day: str) -> list[dict]:
    """
    Best-effort fetch of FF calendar JSON endpoint for one day.
    day: YYYY-MM-DD
    Returns list of event dicts.
    """
    # FF calendar API (public, used by many retail tools)
    # Format: https://nfs.faireconomy.media/ff_calendar_thisweek.json
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    req = Request(url, headers={"User-Agent": "ict-agent/1.0"})
    with urlopen(req, timeout=12) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    events = []
    for row in data if isinstance(data, list) else []:
        # Expected keys: title, country, date, impact, forecast, previous, actual
        date_str = str(row.get("date") or row.get("dateUtc") or "")
        # Normalize to YYYY-MM-DD
        day_match = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
        if not day_match:
            continue
        if day_match.group(1) != day:
            continue
        impact = str(row.get("impact") or "Low").strip().lower()
        events.append({
            "title": row.get("title") or row.get("event") or "Unknown",
            "country": row.get("country") or row.get("currency") or "",
            "datetime": date_str,
            "impact": impact,
            "forecast": row.get("forecast"),
            "previous": row.get("previous"),
            "actual": row.get("actual"),
        })
    return events


def get_economic_calendar(
    date: str | None = None,
    currencies: list[str] | None = None,
    min_impact: str = "medium",
) -> dict:
    """
    date: YYYY-MM-DD (default: today UTC)
    currencies: optional filter e.g. ["USD","GBP","EUR"]
    min_impact: low | medium | high
    """
    day = _parse_date(date)
    min_rank = _IMPACT_RANK.get((min_impact or "medium").lower(), 2)
    currencies_u = [c.upper() for c in (currencies or [])]

    error = None
    events: list[dict] = []
    try:
        events = _fetch_forexfactory_day(day)
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, ValueError) as e:
        error = f"live_calendar_unavailable: {type(e).__name__}: {e}"

    filtered = []
    for ev in events:
        imp = str(ev.get("impact") or "low").lower()
        if _IMPACT_RANK.get(imp, 0) < min_rank:
            continue
        country = str(ev.get("country") or "").upper()
        if currencies_u and country not in currencies_u:
            # also allow currency codes embedded in title region
            if not any(c in country for c in currencies_u):
                continue
        filtered.append(ev)

    high_impact = [e for e in filtered if str(e.get("impact")).lower() == "high"]
    return {
        "date": day,
        "min_impact": min_impact,
        "currencies_filter": currencies_u or "ALL",
        "source": "forexfactory_thisweek_json" if not error else "unavailable",
        "error": error,
        "event_count": len(filtered),
        "high_impact_count": len(high_impact),
        "events": filtered,
        "agent_instruction": (
            "Emit KEY_EVENTS / KEY_EVENTS_TODAY from this list. "
            "If error is set or events is empty, state KEY_EVENTS: UNKNOWN "
            "and reduce confidence into timed windows; do NOT invent releases."
        ),
    }


def _handle(tool_input: dict, ctx) -> dict:
    date = tool_input.get("date")
    currencies = tool_input.get("currencies")
    min_impact = tool_input.get("min_impact") or "medium"
    if isinstance(currencies, str):
        currencies = [c.strip() for c in currencies.split(",") if c.strip()]
    return get_economic_calendar(date=date, currencies=currencies, min_impact=min_impact)


PLUGINS = [
    ToolPlugin(
        name="get_economic_calendar",
        description=(
            "Fetch economic calendar events for a date (default today). "
            "Use before locking Weekly Narrative (KEY_EVENTS) or Daily Bias "
            "(KEY_EVENTS_TODAY). Filter by currencies (USD,GBP,EUR,…) and min_impact "
            "(low|medium|high). High-impact events time ICT profile delivery."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "YYYY-MM-DD (default: today UTC)",
                },
                "currencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional country/currency filters, e.g. [\"USD\",\"GBP\"]",
                },
                "min_impact": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Minimum impact to include (default medium)",
                },
            },
            "required": [],
        },
        handler=_handle,
    ),
]
