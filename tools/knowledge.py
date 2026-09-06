"""
Knowledge / RAG tool for the ICT Agent.

First version: keyword + metadata retrieval over local markdown/JSONL chunks.
Later: swap in embeddings without changing the tool interface the agent sees.
"""
from __future__ import annotations
import os
import re
import json
from pathlib import Path
from harness.plugin import ToolPlugin

KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent / "knowledge"
CHUNKS_DIR = KNOWLEDGE_ROOT / "chunks"
RAW_DIR = KNOWLEDGE_ROOT / "raw"


def _iter_text_files(root: Path):
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.suffix.lower() in {".md", ".txt", ".jsonl"} and p.is_file():
            yield p


def _simple_score(query: str, text: str) -> float:
    """Very lightweight keyword score – good enough until embeddings arrive."""
    q_terms = set(re.findall(r"[a-z0-9_]+", query.lower()))
    if not q_terms:
        return 0.0
    t = text.lower()
    hits = sum(1 for term in q_terms if term in t)
    return hits / len(q_terms)


def _load_chunks() -> list[dict]:
    """Load pre-chunked entries from the JSONL index."""
    chunks_file = CHUNKS_DIR / "all_chunks.jsonl"
    if not chunks_file.exists():
        return []
    chunks = []
    with open(chunks_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return chunks


def search_ict_knowledge(
    query: str,
    topics: list[str] | None = None,
    stage: str | None = None,
    top_k: int = 6,
) -> list[dict]:
    """
    Search the chunked knowledge base.
    
    Uses keyword matching over pre-chunked JSONL with topic bonuses.
    Returns ranked results sorted by relevance score.
    """
    chunks = _load_chunks()
    if not chunks:
        # Fallback to raw-file scanning
        results = []
        for root in [RAW_DIR]:
            for fp in _iter_text_files(root):
                try:
                    text = fp.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                score = _simple_score(query, text)
                if topics:
                    topic_bonus = sum(1 for t in topics if t.lower() in text.lower())
                    score += 0.15 * topic_bonus
                if score <= 0:
                    continue
                excerpt = text[:1200] + ("..." if len(text) > 1200 else "")
                results.append({
                    "source": fp.name,
                    "path": str(fp.relative_to(KNOWLEDGE_ROOT)),
                    "score": round(score, 3),
                    "excerpt": excerpt,
                })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    q_terms = set(re.findall(r"[a-z0-9_]+", query.lower()))
    scored = []
    for chunk in chunks:
        text = chunk.get("text", "")
        chunk_topics = chunk.get("topics", [])

        if q_terms:
            text_lower = text.lower()
            hits = sum(1 for term in q_terms if term in text_lower)
            score = hits / len(q_terms)
        else:
            score = 0.0

        if score <= 0:
            continue

        if topics:
            topic_match = sum(
                1 for t in topics
                if any(t.lower() in ct.lower() for ct in chunk_topics)
            )
            score += 0.25 * topic_match

        if stage:
            stage_match = sum(
                1 for t in chunk_topics if t.lower() == stage.lower()
            )
            score += 0.4 * stage_match

        src_type = chunk.get("source_type", "")
        if src_type in ("lecture", "transcript_clean", "transcript_vtt"):
            score += 0.15

        scored.append({
            "id": chunk["id"],
            "type": chunk.get("type", "unknown"),
            "source": chunk.get("source", ""),
            "source_type": src_type,
            "score": round(score, 3),
            "topics": chunk_topics,
            "excerpt": text[:1000] + ("..." if len(text) > 1000 else ""),
            "tokens": chunk.get("tokens_estimated", 0),
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:top_k]


def _handle_search(tool_input: dict, ctx) -> dict:
    query = tool_input.get("query", "")
    topics = tool_input.get("topics")
    stage = tool_input.get("stage")
    top_k = int(tool_input.get("top_k", 6))
    hits = search_ict_knowledge(query, topics=topics, stage=stage, top_k=top_k)
    return {"query": query, "hits": hits, "count": len(hits)}


PLUGINS = [
    ToolPlugin(
        name="search_ict_knowledge",
        description=(
            "Search the ICT knowledge base (lecture transcripts, doctrine documents, "
            "timestamped claims). Use before forming Weekly Narrative or Daily Bias "
            "so answers stay grounded in ICT's actual teaching. "
            "Optional filters: topics (list of strings), stage (e.g. weekly_narrative)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language or keyword query"},
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional topic filters, e.g. ['bellwether','15m','continuous']",
                },
                "stage": {
                    "type": "string",
                    "description": "Optional stage hint: weekly_narrative | daily_bias | ltf_entry | ...",
                },
                "top_k": {"type": "integer", "default": 6},
            },
            "required": ["query"],
        },
        handler=_handle_search,
    ),
]
