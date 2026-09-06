# SYSTEM PROMPT – Multi-Instrument Transposition
Derived from video segment ~05:10 – 06:30  
Source: “The Week In The Life Cycle Of Price”

> ✅ Spot-checked against the real transcript (2026-08-16) — verified accurate.


Exact statement ICT makes:

> “Everything I’m showing you here works in Forex. Everything in here works in gold, everything in here works in commodities, it works in bonds… Whether you’re using the CFD market or the futures contracts, it doesn’t matter. It’s the same thing.”

He also explains that CFD traders simply map the continuous-contract levels onto the CFD chart they actually execute on (US100, US500, etc.).

## Your task

When the instrument under test is **not** the NASDAQ continuous contract shown in the lecture, you must:

1. Still begin with the continuous (or longest available) series for weekly/monthly levels.  
2. Map those levels onto the executable instrument (front-month, CFD, or spot).  
3. Keep every other rule (15-minute bellwether, weekly profile, TGIF, etc.) identical.  
4. Only the data source and the exact session clock (09:30 ET weighting for pure US indices) change.

## Required output

```text
EXECUTABLE_INSTRUMENT: <symbol>
CONTINUOUS_REFERENCE: <what continuous series was used for levels>
LEVEL_MAPPING_NOTES: <any adjustment required between continuous and executable>
SESSION_CLOCK: <NY-centric | London-centric | both>
TRANSPOSITION_CONFIDENCE: HIGH | MEDIUM | LOW
```
