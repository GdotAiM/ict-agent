#!/usr/bin/env python3
"""
ICT Knowledge Base Ingestion Pipeline

Populates `ict_agent/knowledge/` from:
  1. Local ICT Knowledge Centre (Desktop/markdown archive)
  2. Video transcripts (smc-icm-trading/shared/ict_videos/)
  3. Optional YouTube downloads (2016 mentorship, legacy content)

Output structure:
  knowledge/raw/       — immutable source copies
  knowledge/chunks/    — structured JSONL chunks with metadata
  knowledge/indexes/   — keyword index + (future) vector index
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_ROOT = BASE_DIR / "knowledge"
RAW_DIR = KNOWLEDGE_ROOT / "raw"
CHUNKS_DIR = KNOWLEDGE_ROOT / "chunks"
INDEXES_DIR = KNOWLEDGE_ROOT / "indexes"

# Source directories to scan
SOURCE_DIRS = [
    r"C:\Users\cash\Desktop\ICT Knowledge Centre",
    r"C:\Users\cash\smc-icm-trading\shared\ict_videos\transcripts",
    str(BASE_DIR / "docs"),
    str(BASE_DIR / "knowledge" / "raw"),
]

# YouTube IDs to search/download (2016 private mentorship era)
# These are known lectures from the 2016 series — add more as needed
YOUTUBE_2016_PLAYLISTS = [
    # "PL..." style playlist IDs — user can fill these in
]

YOUTUBE_SEARCH_QUERIES = [
    "ICT 2016 private mentorship full lecture",
    "ICT 2016 silver bullet tutorial",
    "ICT 2016 market maker model",
    "ICT 2016 optimal trade entry",
    "Inner Circle Trader 2016 mentorship",
]

# ---------------------------------------------------------------------------
# Chunk types and their split strategies
# ---------------------------------------------------------------------------

CHUNK_TYPES = {
    "doctrine": {
        "max_tokens": 400,
        "min_tokens": 50,
        "split_on": "heading",       # split on ## or ### headings
        "priority": 1.0,
    },
    "process": {
        "max_tokens": 600,
        "min_tokens": 80,
        "split_on": "numbered_list",  # split on 1. 2. 3. steps
        "priority": 0.9,
    },
    "example": {
        "max_tokens": 800,
        "min_tokens": 100,
        "split_on": "section",       # split on ### sections
        "priority": 0.7,
    },
    "claim": {
        "max_tokens": 200,
        "min_tokens": 20,
        "split_on": "sentence",      # sentence-level chunks
        "priority": 0.8,
    },
}

# ---------------------------------------------------------------------------
# Topic taxonomies — used for metadata tagging
# ---------------------------------------------------------------------------

TOPIC_INDEXES = {
    # Stage relevance
    "weekly_narrative": {"keywords": ["weekly profile", "week ahead", "weekly bias", "setup of the week"]},
    "daily_bias": {"keywords": ["daily bias", "daily profile", "overnight", "daily setup"]},
    "ltf_entry": {"keywords": ["entry", "trigger", "fvg", "order block", "15m", "5m", "1m", "displacement"]},
    "timing": {"keywords": ["kill zone", "london", "ny am", "ny pm", "asian", "time", "session"]},
    "risk_exec": {"keywords": ["risk", "position size", "stop loss", "take profit", "confluence", "trade management"]},
    # ICT concepts
    "bos": {"keywords": ["break of structure", "bos", "continuation"]},
    "choch": {"keywords": ["change of character", "choch", "mss", "market structure shift"]},
    "fvg": {"keywords": ["fair value gap", "fvg", "imbalance", "liquidity void"]},
    "ifvg": {"keywords": ["inverse fair value gap", "ifvg", "inversion fvg"]},
    "ob": {"keywords": ["order block", "ob ", "mitigation block"]},
    "breaker": {"keywords": ["breaker block", "breakers", "failed order block"]},
    "liquidity": {"keywords": ["liquidity", "bsl", "ssl", "buy side liquidity", "sell side liquidity", "equal highs", "equal lows", "stop hunt", "sweep"]},
    "pd_array": {"keywords": ["premium", "discount", "equilibrium", "pd array", "dealing range", "otp", "otd", "50%"]},
    "ote": {"keywords": ["optimal trade entry", "ote", "fibonacci", "fib", "0.618", "0.62", "0.786"]},
    "silver_bullet": {"keywords": ["silver bullet", "sb", "10am", "11am", "2pm", "time based"]},
    "power_of_3": {"keywords": ["power of 3", "amd", "accumulation manipulation distribution", "open close"]},
    " Judas": {"keywords": ["judas swing", "fake out", "manipulation leg"]},
    "bread_and_butter": {"keywords": ["bread and butter", "bab", "simple setup", "classic"]},
    "macro_time": {"keywords": ["macro time", "algorithmic theory", "delivery", "time based delivery"]},
    # Instruments
    "forex": {"keywords": ["forex", "currency", "eurusd", "gbpusd", "major pairs"]},
    "indices": {"keywords": ["nasdaq", "NQ", "nas100", "sp500", "SPY", "indices", "index"]},
    "crypto": {"keywords": ["bitcoin", "btc", "crypto", "ethereum", "eth"]},
    "commodities": {"keywords": ["gold", "xauusd", "silver", "oil", "commodities"]},
}


def detect_topics(text: str, source_type: str) -> list[str]:
    """Auto-detect relevant topics for a chunk based on content."""
    text_lower = text.lower()
    detected = []

    # Stage relevance
    for topic, info in TOPIC_INDEXES.items():
        if any(kw in text_lower for kw in info["keywords"]):
            detected.append(topic)

    # Source type adds implicit topics
    if source_type == "lecture":
        detected.append("mentorship")
    elif source_type == "tutorial":
        detected.append("tutorial")
    elif source_type == "transcript":
        detected.append("video_transcript")

    return list(set(detected))


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Chunking strategies
# ---------------------------------------------------------------------------

def chunk_by_heading(text: str, min_tokens: int, max_tokens: int) -> list[str]:
    """Split on ## or ### Markdown headings."""
    pattern = re.compile(r"^#{2,3}\s+.+$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if estimate_tokens(chunk) >= min_tokens:
            chunks.append(chunk)

    # Fallback: whole document if no headings found
    if not chunks and estimate_tokens(text) >= min_tokens:
        chunks.append(text.strip())

    return chunks


def chunk_by_numbered_list(text: str, min_tokens: int, max_tokens: int) -> list[str]:
    """Split on numbered step lists (1., 2., 3., ...)."""
    pattern = re.compile(r"^(\d+\.\s+.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    chunks = []
    current = []
    for m in matches:
        if current:
            block = "\n".join(current).strip()
            if estimate_tokens(block) >= min_tokens:
                chunks.append(block)
            current = []
        current.append(m.group(1))

    if current:
        block = "\n".join(current).strip()
        if estimate_tokens(block) >= min_tokens:
            chunks.append(block)

    if not chunks and estimate_tokens(text) >= min_tokens:
        chunks.append(text.strip())

    return chunks


def chunk_by_section(text: str, min_tokens: int, max_tokens: int) -> list[str]:
    """Split on ### level headings (subsection level)."""
    pattern = re.compile(r"^#{3,4}\s+.+$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if estimate_tokens(chunk) >= min_tokens:
            chunks.append(chunk)

    if not chunks and estimate_tokens(text) >= min_tokens:
        chunks.append(text.strip())

    return chunks


def chunk_by_sentence(text: str, min_tokens: int, max_tokens: int) -> list[str]:
    """Sentence-level chunks for claim-style extraction."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = []
    for s in sentences:
        current.append(s)
        block = " ".join(current)
        if estimate_tokens(block) >= min_tokens:
            chunks.append(block.strip())
            current = []
    if current:
        block = " ".join(current).strip()
        if block and estimate_tokens(block) >= min_tokens:
            chunks.append(block)
    return chunks


SPLIT_STRATEGIES = {
    "heading": chunk_by_heading,
    "numbered_list": chunk_by_numbered_list,
    "section": chunk_by_section,
    "sentence": chunk_by_sentence,
}


# ---------------------------------------------------------------------------
# Source discovery
# ---------------------------------------------------------------------------

def discover_sources() -> list[dict]:
    """Find all ingestible source files."""
    sources = []

    for src_dir in SOURCE_DIRS:
        src_path = Path(src_dir)
        if not src_path.exists():
            continue

        for root, dirs, files in os.walk(src_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("__pycache__",)]
            for fname in files:
                fpath = Path(root) / fname
                ext = fpath.suffix.lower()

                if ext not in (".md", ".txt", ".json", ".vtt", ".jsonl"):
                    continue

                rel = fpath.relative_to(src_path) if src_path != BASE_DIR else fpath.relative_to(BASE_DIR)

                # Determine source type
                if "transcripts" in str(fpath) and fname.endswith(".vtt"):
                    source_type = "transcript_vtt"
                elif "transcripts" in str(fpath) and fname.endswith(".txt"):
                    source_type = "transcript_clean"
                elif "2024" in str(rel) or "mentorship" in fname.lower():
                    source_type = "lecture"
                elif "knowledge/raw" in str(fpath):
                    source_type = "doctrine"
                elif ext == ".md" and "docs" in str(fpath):
                    source_type = "tutorial"
                elif ext == ".md":
                    source_type = "reference"
                else:
                    source_type = "other"

                sources.append({
                    "path": str(fpath),
                    "rel_path": str(rel),
                    "source_type": source_type,
                    "size_bytes": fpath.stat().st_size,
                })

    return sources


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_vtt(vtt_path: Path) -> str:
    """Parse WebVTT format to plain text."""
    lines = vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    text_parts = []
    for line in lines:
        line = line.strip()
        # Skip timestamp lines and VTT header
        if re.match(r"^\d{2}:\d{2}:\d{2}", line):
            continue
        if line.startswith("WEBVTT") or line == "" or re.match(r"^\d+$", line):
            continue
        # Clean HTML tags if present
        clean = re.sub(r"<[^>]+>", "", line)
        if clean:
            text_parts.append(clean)
    return "\n".join(text_parts)


def extract_text_from_md(md_path: Path) -> tuple[str, dict]:
    """Extract text and frontmatter from markdown."""
    content = md_path.read_text(encoding="utf-8", errors="ignore")
    meta = {}

    # Parse YAML frontmatter if present
    if content.startswith("---"):
        fm_end = content.find("---", 3)
        if fm_end > 0:
            fm_block = content[3:fm_end]
            for line in fm_block.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    meta[key.strip()] = val.strip().strip('"')
            content = content[fm_end + 3:].strip()

    return content, meta


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def create_chunks(text: str, source_type: str, source_path: str, extra_meta: dict | None = None) -> list[dict]:
    """Split text into semantically meaningful chunks with metadata."""
    chunks = []
    chunk_id = 0

    # Choose strategies based on source type
    strategies = []
    if source_type in ("lecture", "transcript_clean", "transcript_vtt"):
        strategies = [
            ("process", "numbered_list"),
            ("example", "section"),
            ("doctrine", "heading"),
        ]
    elif source_type in ("tutorial", "doctrine", "reference"):
        strategies = [
            ("doctrine", "heading"),
            ("claim", "sentence"),
        ]
    else:
        strategies = [("doctrine", "heading")]

    for chunk_type, strategy_name in strategies:
        cfg = CHUNK_TYPES[chunk_type]
        splitter = SPLIT_STRATEGIES[strategy_name]
        raw_chunks = splitter(text, cfg["min_tokens"], cfg["max_tokens"])

        for chunk_text in raw_chunks:
            tokens = estimate_tokens(chunk_text)
            topics = detect_topics(chunk_text, source_type)

            chunks.append({
                "id": f"{chunk_id:04d}",
                "type": chunk_type,
                "source": source_path,
                "source_type": source_type,
                "text": chunk_text,
                "tokens_estimated": tokens,
                "topics": topics,
                "metadata": {
                    **extra_meta,
                    "chunk_type": chunk_type,
                    "strategy": strategy_name,
                },
            })
            chunk_id += 1

    return chunks


# ---------------------------------------------------------------------------
# Keyword indexing
# ---------------------------------------------------------------------------

def build_keyword_index(chunks: list[dict]) -> dict:
    """Build a simple inverted index for keyword search."""
    index: dict[str, list[int]] = {}
    for i, chunk in enumerate(chunks):
        text_lower = chunk["text"].lower()
        terms = set(re.findall(r"[a-z0-9_]{3,}", text_lower))
        for term in terms:
            index.setdefault(term, []).append(i)
    return index


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_ingestion(verbose: bool = True) -> dict:
    """Run the full ingestion pipeline. Returns stats."""
    # Ensure directories exist
    for d in (RAW_DIR, CHUNKS_DIR, INDEXES_DIR):
        d.mkdir(parents=True, exist_ok=True)

    stats = {
        "sources_discovered": 0,
        "sources_copied": 0,
        "chunks_created": 0,
        "total_tokens": 0,
        "errors": [],
    }

    # 1. Discover sources
    sources = discover_sources()
    stats["sources_discovered"] = len(sources)
    if verbose:
        print(f"Discovered {len(sources)} source files")

    # 2. Copy raw sources to knowledge/raw/ (deduplicated)
    seen_paths = set()
    for src in sources:
        src_path = Path(src["path"])
        if not src_path.exists():
            continue

        # Compute destination path
        dest_rel = src["rel_path"]
        dest_path = RAW_DIR / dest_rel
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Skip if already exists and identical
        if dest_path.exists():
            if dest_path.stat().st_size == src_path.stat().st_size:
                continue
        dest_path.write_bytes(src_path.read_bytes())
        stats["sources_copied"] += 1

    # 3. Create chunks
    all_chunks: list[dict] = []
    for src in sources:
        src_path = Path(src["path"])
        if not src_path.exists():
            continue

        try:
            if src["source_type"] == "transcript_vtt":
                text = extract_text_from_vtt(src_path)
                meta = {"video_id": src_path.stem}
            elif src["source_type"] in ("lecture", "tutorial", "doctrine", "reference"):
                text, meta = extract_text_from_md(src_path)
            elif src["source_type"] == "transcript_clean":
                text = src_path.read_text(encoding="utf-8", errors="ignore")
                meta = {}
            else:
                text = src_path.read_text(encoding="utf-8", errors="ignore")
                meta = {}

            chunks = create_chunks(
                text,
                source_type=src["source_type"],
                source_path=src["rel_path"],
                extra_meta=meta,
            )
            all_chunks.extend(chunks)

            if verbose:
                print(f"  [OK] {src['rel_path']}: {len(chunks)} chunks, {sum(c['tokens_estimated'] for c in chunks):,} est tokens")

        except Exception as e:
            stats["errors"].append(f"{src['rel_path']}: {e}")
            if verbose:
                print(f"  [ERR] {src['rel_path']}: {e}")

    stats["chunks_created"] = len(all_chunks)
    stats["total_tokens"] = sum(c["tokens_estimated"] for c in all_chunks)

    # 4. Write chunks as JSONL
    chunks_file = CHUNKS_DIR / "all_chunks.jsonl"
    with open(chunks_file, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # 5. Write chunk index (for fast lookup)
    index_file = CHUNKS_DIR / "chunk_index.json"
    index_data = {c["id"]: {"source": c["source"], "type": c["type"], "topics": c["topics"], "tokens": c["tokens_estimated"]} for c in all_chunks}
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    # 6. Build keyword index
    kw_index = build_keyword_index(all_chunks)
    kw_file = INDEXES_DIR / "keyword_index.json"
    with open(kw_file, "w", encoding="utf-8") as f:
        json.dump(kw_index, f, ensure_ascii=False)

    # 7. Summary manifest
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "stats": stats,
        "chunk_count": len(all_chunks),
        "source_types": {},
    }
    for src in sources:
        st = src["source_type"]
        manifest["source_types"][st] = manifest["source_types"].get(st, 0) + 1

    manifest_file = KNOWLEDGE_ROOT / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ICT Knowledge Base Ingestion Pipeline")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--dry-run", action="store_true", help="Discover sources only, don't write chunks")
    args = parser.parse_args()

    if args.dry_run:
        sources = discover_sources()
        print(f"Would ingest {len(sources)} sources:")
        for s in sources:
            print(f"  [{s['source_type']:20s}] {s['rel_path']} ({s['size_bytes']:,} bytes)")
    else:
        stats = run_ingestion(verbose=args.verbose)
        print(f"\nIngestion complete:")
        print(f"  Sources discovered: {stats['sources_discovered']}")
        print(f"  Sources copied:     {stats['sources_copied']}")
        print(f"  Chunks created:     {stats['chunks_created']}")
        print(f"  Est. tokens:        {stats['total_tokens']:,}")
        if stats["errors"]:
            print(f"  Errors:             {len(stats['errors'])}")
            for e in stats["errors"][:5]:
                print(f"    - {e}")
