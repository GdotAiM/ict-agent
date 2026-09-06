"""
Automated metric logging for the ICT Agent.

Captures, per session / per stage:
  - gate pass / fail / retry counts
  - structured-field completeness (Weekly Bias, Daily Bias, etc.)
  - confluence scores when present
  - trade decisions (TRADE / WATCH / NO_SETUP)
  - simple timing (stage duration when available)

Metrics are written both to:
  1. the session JSONL (so they stay with the full trace)
  2. a small SQLite table (metrics_log) for easy aggregation across weeks
"""
from __future__ import annotations
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import config

_METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    session_id TEXT,
    symbol TEXT,
    mode TEXT,
    week_label TEXT,
    stage TEXT,
    metric_name TEXT NOT NULL,
    metric_value TEXT,
    meta TEXT
);
CREATE INDEX IF NOT EXISTS idx_metrics_session ON metrics_log(session_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics_log(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_symbol ON metrics_log(symbol);
"""


def _conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_metrics_db():
    with _conn() as c:
        c.executescript(_METRICS_SCHEMA)


def log_metric(
    session_id: str,
    symbol: str,
    mode: str,
    metric_name: str,
    metric_value: Any,
    stage: str = "",
    week_label: str = "",
    meta: dict | None = None,
):
    """Write one metric row to SQLite and return the row dict (for session log)."""
    init_metrics_db()
    ts = datetime.now(timezone.utc).isoformat()
    value_str = json.dumps(metric_value, default=str) if not isinstance(metric_value, (str, int, float, bool)) else str(metric_value)
    meta_str = json.dumps(meta or {}, default=str)
    with _conn() as c:
        c.execute(
            """INSERT INTO metrics_log
               (ts, session_id, symbol, mode, week_label, stage, metric_name, metric_value, meta)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ts, session_id, symbol, mode, week_label, stage, metric_name, value_str, meta_str),
        )
    return {
        "ts": ts,
        "session_id": session_id,
        "symbol": symbol,
        "mode": mode,
        "week_label": week_label,
        "stage": stage,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "meta": meta or {},
    }


# ---------------------------------------------------------------------------
# Extractors – pull metrics from stage narratives / gate results
# ---------------------------------------------------------------------------

_STRUCTURED_PATTERNS = {
    "weekly_bias": re.compile(r"WEEKLY_BIAS\s*:\s*(BULLISH|BEARISH|RANGE)", re.I),
    "daily_bias": re.compile(r"DAILY_BIAS\s*:\s*(BULLISH|BEARISH|NEUTRAL)", re.I),
    "draw_on_liquidity": re.compile(r"DRAW_ON_LIQUIDITY\s*:\s*(.+?)(?:\n|$)", re.I),
    "weekly_profile": re.compile(r"WEEKLY_PROFILE\s*:\s*(.+?)(?:\n|$)", re.I),
    "bellwether": re.compile(r"BELLWETHER\s*:\s*(\S+)", re.I),
    "confluence_score": re.compile(r"CONFLUENCE_SCORE\s*:\s*([0-4])", re.I),
    "decision": re.compile(r"DECISION\s*:\s*(TRADE|WATCH|NO_SETUP)", re.I),
    "tgif_behaviour": re.compile(r"TGIF_BEHAVIOUR\s*:\s*(YES|NO|PARTIAL)", re.I),
    "preferred_sessions": re.compile(r"PREFERRED_SESSIONS\s*:\s*(LONDON|NY_AM|BOTH|NONE)", re.I),
    "power_of_3": re.compile(r"POWER_OF_3_PHASE\s*:\s*(ACCUMULATION|MANIPULATION|DISTRIBUTION|UNKNOWN)", re.I),
    "key_events": re.compile(r"KEY_EVENTS(?:_TODAY)?\s*:\s*(.+?)(?:\n|$)", re.I),
    "delivery_note": re.compile(r"DELIVERY_NOTE\s*:\s*(.+?)(?:\n|$)", re.I),
}


def extract_structured_fields(text: str) -> dict[str, str]:
    out = {}
    for name, pat in _STRUCTURED_PATTERNS.items():
        m = pat.search(text or "")
        if m:
            out[name] = m.group(1).strip()
    return out


def record_stage_metrics(
    session,
    symbol: str,
    mode: str,
    stage: str,
    narrative: str,
    gate_passed: bool | None = None,
    gate_reason: str = "",
    week_label: str = "",
    retries: int = 0,
):
    """
    Call after each stage. Writes multiple metric rows and also
    appends a compact 'metrics' event to the session log.
    """
    sid = getattr(session, "session_id", "") or ""
    fields = extract_structured_fields(narrative)

    rows = []
    # Completeness: did the stage emit the fields we care about?
    for field, value in fields.items():
        rows.append(log_metric(sid, symbol, mode, f"field.{field}", value, stage=stage, week_label=week_label))

    if gate_passed is not None:
        rows.append(log_metric(
            sid, symbol, mode, "gate.passed", gate_passed,
            stage=stage, week_label=week_label, meta={"reason": gate_reason},
        ))
    if retries:
        rows.append(log_metric(sid, symbol, mode, "gate.retries", retries, stage=stage, week_label=week_label))

    # Decision-level metrics
    if "decision" in fields:
        rows.append(log_metric(sid, symbol, mode, "decision", fields["decision"], stage=stage, week_label=week_label))
    if "confluence_score" in fields:
        rows.append(log_metric(sid, symbol, mode, "confluence_score", int(fields["confluence_score"]), stage=stage, week_label=week_label))

    # Session log event
    if hasattr(session, "append"):
        session.append("metrics", {
            "stage": stage,
            "fields": fields,
            "gate_passed": gate_passed,
            "gate_reason": gate_reason,
            "retries": retries,
        })

    return rows


def summarise_session(session_id: str) -> dict:
    """Aggregate metrics for one session – useful for end-of-week reports."""
    init_metrics_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT stage, metric_name, metric_value FROM metrics_log WHERE session_id = ?",
            (session_id,),
        ).fetchall()

    summary = {
        "session_id": session_id,
        "gates_passed": 0,
        "gates_failed": 0,
        "total_retries": 0,
        "decisions": [],
        "fields_seen": set(),
        "confluence_scores": [],
    }
    for stage, name, value in rows:
        if name == "gate.passed":
            if value.lower() in ("true", "1"):
                summary["gates_passed"] += 1
            else:
                summary["gates_failed"] += 1
        elif name == "gate.retries":
            try:
                summary["total_retries"] += int(value)
            except ValueError:
                pass
        elif name == "decision":
            summary["decisions"].append(value)
        elif name == "confluence_score":
            try:
                summary["confluence_scores"].append(int(value))
            except ValueError:
                pass
        elif name.startswith("field."):
            summary["fields_seen"].add(name.replace("field.", ""))

    summary["fields_seen"] = sorted(summary["fields_seen"])
    return summary


def export_metrics_csv(path: str = "metrics_export.csv") -> str:
    """Dump the whole metrics_log table to CSV for external analysis."""
    import csv
    init_metrics_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM metrics_log ORDER BY id").fetchall()
        cols = [d[0] for d in c.execute("SELECT * FROM metrics_log LIMIT 0").description]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    return path
