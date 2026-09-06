"""
MEMORY component — SQLite journal + Memory-Augmented Generation (MAG).

Two tiers:
  1. Episodic memory (SQLite): analysis_log + trades tables for exact-match recall.
  2. Semantic memory (MAG): embeddings of every analysis stored in
     analysis_embeddings table. Enables similarity search across past setups.

MAG flow:
  - After each log_analysis(), the narrative is embedded and stored.
  - Before Stage 1 runs, get_similar_setups() fetches K past analyses
    semantically closest to the current market context.
  - The agent sees "what happened before in similar conditions" alongside
    static ICT doctrine from RAG — giving it both teaching and experience.

Embedding provider: OpenRouter (text-embedding-3-small), with SSL bypass
for Python 3.14 on Windows where cert bundles are broken.
"""
from __future__ import annotations
import sqlite3
import json
import math
import os
import struct
import ssl
import config
from datetime import datetime, timezone
from harness.plugin import ToolPlugin

# ---------------------------------------------------------------------------
# SSL bypass for Python 3.14 / Windows cert store issues
# ---------------------------------------------------------------------------

def _ssl_bypass():
    """Apply SSL certificate bypass globally for HTTPS calls."""
    if getattr(_ssl_bypass, "_done", False):
        return
    _ssl_bypass._done = True
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass


_ssl_bypass()

# Also patch httpx (used by openai SDK) and urllib.request
try:
    import httpx
    _orig_transport = httpx.HTTPTransport
    class _SSLDisabledTransport(_orig_transport):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault('ssl', False)
            super().__init__(*args, **kwargs)
    httpx.HTTPTransport = _SSLDisabledTransport
except Exception:
    pass

try:
    import urllib.request
    _orig_opener = urllib.request.build_opener
    def _patched_build_opener():
        return urllib.request.OpenerDirector()
    urllib.request._opener = None
except Exception:
    pass

# ---------------------------------------------------------------------------
# DB schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    trend TEXT,
    zone TEXT,
    in_kill_zone INTEGER,
    decision TEXT,
    narrative TEXT
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT,
    entry REAL,
    stop REAL,
    target REAL,
    qty INTEGER,
    order_id TEXT,
    outcome TEXT DEFAULT 'open',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS analysis_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    embedding BLOB NOT NULL,
    bias TEXT,
    trigger_type TEXT,
    zone TEXT,
    decision TEXT,
    summary TEXT,
    FOREIGN KEY (analysis_id) REFERENCES analysis_log(id)
);
"""

_EMBEDDING_DIM = 1536  # text-embedding-3-small


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _setup_cosine_similarity(conn):
    """Register cosine_similarity as a SQLite UDF for ANN queries."""
    def _cos_sim(a_bytes, b_bytes):
        try:
            dim = len(a_bytes) // 4
            a = _blob_to_vec(a_bytes, dim)
            b = _blob_to_vec(b_bytes, dim)
            return _cosine_similarity(a, b)
        except Exception:
            return 0.0
    conn.create_function("cosine_similarity", 2, _cos_sim)


def _vec_to_blob(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _blob_to_vec(blob: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", blob[: dim * 4]))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _get_embedding_config() -> tuple[str, str] | None:
    """Return (api_key, model) or None if not configured."""
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("EMBEDDINGS_API_KEY") or ""
    model = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-small")
    if not api_key:
        return None
    return api_key, model


def _embed_text(text: str, model: str) -> list[float] | None:
    """Get embedding vector for text via OpenRouter using urllib (avoids httpx SSL issues)."""
    cfg = _get_embedding_config()
    if not cfg:
        return None
    api_key, _ = cfg
    try:
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        payload = json.dumps({"model": model, "input": text}).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/embeddings",
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["data"][0]["embedding"]
    except Exception as e:
        print(f"[MAG] embed failed: {e}")
        return None


def _build_summary(bias: str, trigger_type: str, zone: str,
                   decision: str, narrative: str) -> str:
    """Compact summary string optimized for semantic recall."""
    parts = []
    if bias:
        parts.append(f"{bias} bias")
    if trigger_type:
        parts.append(f"{trigger_type} trigger")
    if zone:
        parts.append(f"{zone} zone")
    if decision:
        parts.append(f"decision={decision}")
    # Append first 200 chars of narrative for context
    clean = "".join(c for c in narrative if ord(c) < 128)[:200]
    if clean.strip():
        parts.append(clean)
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def init_db():
    with _conn() as c:
        c.executescript(_SCHEMA)
        _setup_cosine_similarity(c)


def log_analysis(symbol: str, trend: str, zone: str, in_kill_zone: bool,
                 decision: str, narrative: str) -> dict:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO analysis_log (ts, symbol, trend, zone, in_kill_zone, "
            "decision, narrative) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), symbol, trend, zone,
             int(in_kill_zone), decision, narrative),
        )
        aid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    # Embed and store for MAG
    embed_and_store(aid, symbol, trend, "", zone, decision, narrative)
    return {"logged": True, "analysis_id": aid}


def log_trade(symbol: str, direction: str, entry: float, stop: float,
              target: float, qty: int, order_id: str, notes: str = "") -> dict:
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO trades (ts, symbol, direction, entry, stop, target, "
            "qty, order_id, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), symbol, direction, entry,
             stop, target, qty, order_id, notes),
        )
        conn.commit()
    finally:
        conn.close()
    return {"logged": True}


def get_recent_context(symbol: str, limit: int = 5) -> dict:
    with _conn() as c:
        c.row_factory = sqlite3.Row
        analyses = c.execute(
            "SELECT ts, trend, zone, decision, narrative FROM analysis_log "
            "WHERE symbol = ? ORDER BY id DESC LIMIT ?", (symbol, limit),
        ).fetchall()
        trades = c.execute(
            "SELECT ts, direction, entry, stop, target, outcome FROM trades "
            "WHERE symbol = ? ORDER BY id DESC LIMIT ?", (symbol, limit),
        ).fetchall()
    return {
        "recent_analyses": [dict(r) for r in analyses],
        "recent_trades": [dict(r) for r in trades],
    }


def embed_and_store(
    analysis_id: int,
    symbol: str,
    bias: str,
    trigger_type: str,
    zone: str,
    decision: str,
    narrative: str,
) -> dict | None:
    """Embed an analysis and store the vector for semantic recall."""
    cfg = _get_embedding_config()
    if not cfg:
        return None
    _, model = cfg
    summary = _build_summary(bias, trigger_type, zone, decision, narrative)
    vec = _embed_text(summary, model)
    if vec is None:
        return None
    dim = len(vec)
    with _conn() as c:
        c.execute(
            "INSERT INTO analysis_embeddings "
            "(analysis_id, symbol, embedding, bias, trigger_type, zone, decision, summary) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (analysis_id, symbol, _vec_to_blob(vec), bias, trigger_type,
             zone, decision, summary),
        )
    return {"dim": dim, "stored": True}


def get_similar_setups(symbol: str, k: int = 3,
                       query_text: str = "") -> list[dict]:
    """Find K past analyses semantically similar to query_text for a symbol."""
    cfg = _get_embedding_config()
    if not cfg:
        return []
    if not query_text:
        return []
    _, model = cfg

    vec = _embed_text(query_text, model)
    if vec is None:
        return []

    q_blob = _vec_to_blob(vec)
    dim = len(vec)

    with _conn() as c:
        _setup_cosine_similarity(c)
        rows = c.execute(
            "SELECT ae.embedding, al.id, al.ts, al.symbol, al.trend, al.zone, al.decision, al.narrative "
            "FROM analysis_embeddings ae JOIN analysis_log al ON al.id = ae.analysis_id "
            "WHERE al.symbol = ? ORDER BY cosine_similarity(ae.embedding, ?) DESC LIMIT ?",
            (symbol, q_blob, k),
        ).fetchall()

    results = []
    for row in rows:
        stored_vec = _blob_to_vec(row[0], dim)
        sim = _cosine_similarity(stored_vec, vec)
        results.append({
            "analysis_id": row[1],
            "ts": row[2],
            "symbol": row[3],
            "bias": row[4] or "",
            "trigger_type": "",
            "zone": row[5],
            "decision": row[6],
            "narrative_snippet": (row[7] or "")[:200].replace(chr(10), " "),
            "similarity": round(sim, 3),
        })
    return results


def get_cross_symbol_similar(symbol: str, k: int = 2,
                              query_text: str = "") -> list[dict]:
    """Find similar setups in OTHER symbols (cross-symbol pattern mining)."""
    cfg = _get_embedding_config()
    if not cfg:
        return []
    if not query_text:
        return []
    _, model = cfg

    vec = _embed_text(query_text, model)
    if vec is None:
        return []

    q_blob = _vec_to_blob(vec)
    dim = len(vec)

    with _conn() as c:
        _setup_cosine_similarity(c)
        rows = c.execute(
            "SELECT ae.embedding, al.id, al.ts, al.symbol, al.trend, al.zone, al.decision, al.narrative "
            "FROM analysis_embeddings ae JOIN analysis_log al ON al.id = ae.analysis_id "
            "WHERE al.symbol != ? ORDER BY cosine_similarity(ae.embedding, ?) DESC LIMIT ?",
            (symbol, q_blob, k),
        ).fetchall()

    results = []
    for row in rows:
        stored_vec = _blob_to_vec(row[0], dim)
        sim = _cosine_similarity(stored_vec, vec)
        results.append({
            "analysis_id": row[1],
            "ts": row[2],
            "symbol": row[3],
            "bias": row[4] or "",
            "trigger_type": "",
            "zone": row[5],
            "decision": row[6],
            "narrative_snippet": (row[7] or "")[:200].replace(chr(10), " "),
            "similarity": round(sim, 3),
        })
    return results


def batch_embed_existing(limit: int = 100) -> dict:
    """Backfill embeddings for all unembedded analysis_log entries.
    Call this once after deployment to populate the vector store."""
    with _conn() as c:
        rows = c.execute(
            """SELECT al.id, al.symbol, al.trend, al.zone, al.decision, al.narrative
               FROM analysis_log al
               LEFT JOIN analysis_embeddings ae ON ae.analysis_id = al.id
               WHERE ae.id IS NULL
               LIMIT ?""",
            (limit,),
        ).fetchall()
        pending = rows
    success, failed = 0, 0
    for row in pending:
        aid, sym, trend, zone, dec, narr = row
        try:
            embed_and_store(aid, sym, trend, "", zone, dec, narr or "")
            success += 1
        except Exception:
            failed += 1
    return {"success": success, "failed": failed, "total_pending": len(pending)}


# ---------------------------------------------------------------------------
# Plugin handlers
# ---------------------------------------------------------------------------

def _handle_get_recent_context(tool_input: dict, ctx) -> dict:
    return get_recent_context(tool_input["symbol"])


def _handle_log_analysis(tool_input: dict, ctx) -> dict:
    return log_analysis(
        symbol=tool_input["symbol"], trend=tool_input["trend"],
        zone=tool_input["zone"], in_kill_zone=tool_input["in_kill_zone"],
        decision=tool_input["decision"], narrative=tool_input["narrative"],
    )


PLUGINS = [
    ToolPlugin(
        name="get_recent_context",
        description=(
            "Returns this symbol's recent analysis log and trade history from "
            "memory, for continuity across runs."
        ),
        input_schema={
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
        handler=_handle_get_recent_context,
    ),
    ToolPlugin(
        name="log_analysis",
        description=(
            "Logs this reasoning pass to memory (even if no trade was taken). "
            "Always call this before ending your turn so future analyses can "
            "learn from past context."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "trend": {"type": "string"},
                "zone": {"type": "string"},
                "in_kill_zone": {"type": "boolean"},
                "decision": {"type": "string", "enum": ["trade", "watch", "no_setup"]},
                "narrative": {"type": "string"},
            },
            "required": ["symbol", "trend", "zone", "in_kill_zone", "decision", "narrative"],
        },
        handler=_handle_log_analysis,
    ),
]
