# RAG / Knowledge Layer for the ICT Agent

## Goal

Make the agent able to **digest and retrieve** long-form ICT material:

- Full lecture transcripts (this video and future ones)
- The grounded doctrine documents we already wrote
- Timestamped claim sheets
- Future lecture notes ICT releases

…without stuffing 10 000+ tokens into the system prompt on every run.

The knowledge lives **outside** the prompt.  
At runtime the agent (or a dedicated retrieval step) pulls only the relevant slices.

---

## 1. Folder layout (new)

```
ict_agent/
├── knowledge/
│   ├── raw/                  # original source files (never edited)
│   │   ├── 2026-08-15_week_in_the_life_cycle_of_price.md
│   │   ├── 2026-08-15_transcript_raw.txt
│   │   └── ...
│   ├── chunks/               # cleaned, chunked, metadata-rich pieces
│   │   ├── doctrine/
│   │   ├── transcripts/
│   │   └── lecture_notes/
│   └── indexes/              # vector index + optional BM25 / keyword index
│
├── docs/                     # human-readable doctrine (what we already have)
│   ├── ICT_WEEKLY_DAILY_WORKFLOW.md          # current identity doc
│   ├── archive/                              # previous versions of the same doc
│   └── RAG_KNOWLEDGE_LAYER.md                # this file
│
├── tools/
│   └── knowledge.py          # retrieval tool(s) the agent can call
│
└── ...
```

---

## 2. What goes into `knowledge/raw/`

| Source | How we store it |
|--------|-----------------|
| YouTube lecture | Full cleaned transcript + title + date + URL |
| Our grounded MDs | The three/four versions we produced (timestamped claims, identity doctrine, etc.) |
| Future ICT notes | Whatever text / PDF / MD you drop in |

Raw files are immutable. All processing happens downstream.

---

## 3. Chunking strategy (critical for ICT material)

ICT lectures are long, repetitive, and full of “while I’m on this chart…” digressions.  
Naïve 500-token sliding windows lose the thread.

Recommended chunk types:

1. **Doctrine chunks**  
   - Extracted rules, definitions, hierarchies  
   - Example: “15-minute is the bellwether”, “analysis begins on continuous contract”

2. **Process chunks**  
   - Step-by-step operating sequences  
   - Example: weekend preparation sequence, daily bias formation sequence

3. **Example / walk-through chunks**  
   - Specific days or price sequences he walks in the video  
   - Keep enough surrounding context so the example still makes sense

4. **Timestamped claim chunks**  
   - Short, high-precision facts with the approximate timestamp  
   - Ideal for exact retrieval (“what did he say about the 15-minute?”)

Each chunk carries metadata:

```json
{
  "source": "2026-08-15_week_in_the_life_cycle_of_price",
  "type": "doctrine | process | example | claim",
  "timestamp_approx": "11:30",
  "topics": ["bellwether", "15m", "weekly_range"],
  "instruments": ["NQ", "continuous"],
  "stage_relevance": ["weekly_narrative", "daily_bias", "ltf_entry"]
}
```

---

## 4. Retrieval tool the agent can call

Add a new tool (or set of tools) that the staged chain can invoke:

```python
# tools/knowledge.py (sketch)

def search_ict_knowledge(
    query: str,
    topics: list[str] | None = None,
    stage: str | None = None,          # "weekly_narrative", "daily_bias", ...
    top_k: int = 6
) -> list[dict]:
    """
    Hybrid retrieval (vector + keyword) over the knowledge base.
    Returns short, cited passages the model can read.
    """
```

Usage inside a stage prompt:

> “Before you form the Weekly Narrative, call `search_ict_knowledge`  
> with query=‘weekly profile continuous contract previous week high low’  
> and stage=‘weekly_narrative’.  
> Use only the returned passages plus the live market data.”

This keeps the system prompt small while still giving the model the exact language and rules from the lecture.

---

## 5. How the existing documents fit

| Document we already wrote | Where it lives | Role in RAG |
|---------------------------|----------------|-------------|
| Latest identity doctrine (`ICT_WEEKLY_DAILY_WORKFLOW.md`) | `docs/` + also chunked into `knowledge/chunks/doctrine/` | Primary “how ICT thinks” source |
| Timestamp-referenced version | `docs/archive/` + chunked | High-precision claim retrieval |
| Earlier workflow drafts | `docs/archive/` | Historical reference; lower retrieval weight |
| Full video transcript | `knowledge/raw/` → chunked | Source of truth for examples and wording |

All of them become searchable.  
The agent never has to “remember” the whole video; it retrieves the relevant slice at the moment it needs it.

---

## 6. Ingestion pipeline (one-time + ongoing)

```
1. Drop raw transcript or MD into knowledge/raw/
2. Run ingest script:
   - clean
   - split into the four chunk types above
   - attach metadata
   - embed (OpenAI / Voyage / local model – provider-agnostic)
   - write to knowledge/chunks/ and update the index in knowledge/indexes/
3. Agent can immediately call search_ict_knowledge
```

Future lectures = repeat step 1–2.  
No code changes to the agent loop required.

---

## 7. Where this sits in the five-component architecture

| Component | Change |
|-----------|--------|
| **Tools** | New `search_ict_knowledge` (and maybe `get_doctrine_summary`) |
| **Instructions** | Short system prompt that *tells* the model it has a knowledge base and must retrieve before answering doctrine questions |
| **Memory** | Short-term = session log; long-term = the vector store + the structured weekly narrative we already persist |
| **Runtime** | No change to the staged loop except that stages may now call the knowledge tool |
| **LLM** | Unchanged |

---

## 8. Practical next steps (ordered)

1. Create the `knowledge/` folder tree (done in this scaffold).  
2. Move the current doctrine MD + the timestamped version into `knowledge/raw/` and `docs/archive/`.  
3. Write a simple ingest script that:
   - chunks by heading / timestamp / topic
   - writes JSONL chunks with metadata
4. Implement `tools/knowledge.py` with a first version that does **keyword + metadata filtering** (no embeddings yet).  
   This already gives high-precision retrieval for “bellwether”, “continuous contract”, “TGIF”, etc.  
5. Later swap in real embeddings when you want semantic search.  
6. Update Stage 0a / 0b prompts so they are required to call the knowledge tool before emitting the structured Weekly / Daily artefacts.

---

## 9. Why this solves the “too many components” problem

- The video’s full richness stays in the knowledge base, not in the prompt.  
- The agent only loads the 3–8 most relevant passages for the current stage.  
- Future two-hour lectures are just new raw files.  
- The identity we wrote remains the high-level constitution; the RAG layer supplies the detailed case law.

This is the RAG side of the harness.  
Once the folder structure and the first retrieval tool exist, we can start feeding the actual transcript and the doctrine documents we already produced.
