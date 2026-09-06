# ICT Agent — staged prompt-chaining + output validation + codegen

A fully-wired AI agent that trades ICT (Inner Circle Trader / Smart Money
Concepts) setups and can also generate reliable Python helper scripts.
Paper trading only, via Alpaca.

Implements the Udacity AI Engineering patterns:

- **Prompt Chaining** (sequential stages)
- **Gate Checks** (format / content / logic)
- **Retry-with-feedback** (inject failure reason and re-run the same step)
- **Code-generation chain** (outline → code → `ast` syntax gate → refine)

| Component | File(s) |
|---|---|
| LLM | `harness/model_adapters.py` |
| Tools | `tools/*.py` |
| Instructions | `instructions.py` |
| Memory | `memory/store.py` + `harness/session_log.py` |
| Analysis chain | `harness/chained_loop.py` + `agent/gates.py` |
| Codegen chain | `harness/codegen_loop.py` + `agent/codegen_gates.py` |
| Runtime | `agent/runtime.py` |

---

## 1. ICT Analysis Chain (default)

```
Stage 1  HTF Bias          structure + liquidity + PD array
           ↓ gate_htf_bias (hard) ── retry with feedback
Stage 2  Timing & Context  kill zones + memory
           ↓ gate_timing (soft)
Stage 3  LTF Entry Model   FVG / OB after liquidity sweep
           ↓ gate_ltf_entry (hard) ── retry with feedback
Stage 4  Risk & Decision   confluence bar → trade or watch
           ↓ gate_confluence (hard)
```

```bash
python main.py                  # whole watchlist, chained
python main.py SPY              # single symbol
python main.py --free SPY       # original free ReAct loop
```

---

## 2. Codegen Chain (new)

Exactly the Udacity “Data Analysis Script Generation” use-case, tailored
for ICT workflows:

```
Step 1  Outline
          ↓ gate_outline  (list format + read/process/write verbs)
Step 2  Generate code from outline
          ↓ gate_code_syntax  (ast.parse + import allow-list)
Step 3  (on failure) Refine with exact error feedback
          ↓ re-run gate_code_syntax  (up to GATE_MAX_RETRIES)
```

```bash
python main.py codegen "Write a script that reads a session JSONL and writes a CSV trade journal with columns: ts, stage, decision, confluence_score"

python main.py codegen "Write a pandas script that loads 1h candles for a symbol and flags bullish BOS + FVG in discount"

python main.py codegen "Create a simple markdown reporter that summarises the last N session logs"
```

### What the codegen gates enforce

| Gate | Checks |
|---|---|
| `gate_outline` | Numbered/bulleted list + presence of read / process / write (or ICT equivalents) |
| `gate_code_syntax` | `ast.parse()` succeeds + only allowed imports (csv, json, pandas, numpy, …) |

On failure the exact error (SyntaxError message or disallowed import list) is
injected back into the prompt and the step is retried.

---

## Config knobs

```python
GATE_MAX_RETRIES = 2                    # shared by both chains
GATE_HARD_STOP_ON_EXHAUST = True
```

Also available via env: `ICT_GATE_MAX_RETRIES`, `ICT_GATE_HARD_STOP`.

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# ANTHROPIC_API_KEY + Alpaca paper keys
```

## Session inspection

```bash
python main.py sessions
python main.py replay <session.jsonl>
python main.py fork <session.jsonl> 5
```

Every gate result, retry, and final artefact is recorded in the session log.

---

## Disclaimer

Educational scaffold. Paper trading only. Not financial advice.


---

## Feedback-loop brief (Phase A)

Gather a complete **RUN_SPEC** before analysis (Udacity agent feedback loop):

```bash
python main.py brief
```

Checklist: INSTRUMENT, MODE, WEEK_LABEL, RISK_PCT, SESSION_FOCUS, NEWS_POLICY.

- Asks **one** question at a time when fields are missing.
- Emits structured `RUN_SPEC` when complete; optional hand-off to forward/backtest/chained.
- Prompt: `prompts/feedback_loop/requirements_gatherer/system.md` (portable to Bedrock Agent + User input).
