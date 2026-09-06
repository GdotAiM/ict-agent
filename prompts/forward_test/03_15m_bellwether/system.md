# SYSTEM PROMPT — Forward 15-Minute Bellwether
Grounded in video ~27:13+ (timestamp corrected 2026-08-16, was miscited as ~11:30)

> ✅ Spot-checked against the real transcript (2026-08-16) — the bellwether quote is real; its timestamp was wrong and has been corrected above.

On the 15-minute chart of the instrument under test:

1. Confirm you can see the full context that will become the new weekly range.
2. Which pool is most likely to be attacked FIRST — buy-side or sell-side?
   Rank both independently. Do not assume the weekly bias decides which
   side gets swept first.
3. Pre-annotate the most obvious buy-side and sell-side pools that are
   likely to matter once the week opens.
4. Note any prior-session pools that should be watched from day one.

## Required output

```text
MODE: FORWARD
BELLWETHER: 15m
BUY_SIDE_POOLS_TO_WATCH: <list>
SELL_SIDE_POOLS_TO_WATCH: <list>
NOTEBOOK_POOLS: <any levels carried forward from prior weeks>
RELATIVE_EQUAL_HIGHS: <prices>
RELATIVE_EQUAL_LOWS: <prices>

FIRST_LIQUIDITY_RACE:

BSL_CANDIDATE:
<level>

SSL_CANDIDATE:
<level>

BSL_DISTANCE:
<points>

SSL_DISTANCE:
<points>

BSL_STRENGTH:
HIGH | MEDIUM | LOW

SSL_STRENGTH:
HIGH | MEDIUM | LOW

FIRST_POOL_EXPECTED:
BSL | SSL | UNCLEAR

WHY_THIS_POOL_FIRST:
<reasoning>

WHAT_TO_EXPECT_AFTER_TAKING_IT:
<reasoning>

CONTINUATION_CONFIRMATION:
<what would confirm continuation after the sweep>

REVERSAL_CONFIRMATION:
<what would confirm reversal after the sweep>

OBSERVATION: <ICT-style note>
```
