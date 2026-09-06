---
title: "ICT Breaker Block Trading — Failed Order Block Strategy (Free PDF)"
source: "https://innercircletrader.net/tutorials/ict-breaker-block-trading/"
type: "tutorial"
date: "2024-10-26T05:46:37"
modified: "2026-07-02T16:05:54"
categories:
  - "ICT Trading Tutorials"
tags:
  - "Breaker block"
  - "breaker block trading"
  - "ICT breaker block"
excerpt: "An ICT Breaker Block is a failed order block — an order block that price has broken through, which then flips and acts as support or resistance from the opposite side. It is one of three “block trio” PD Arrays in the ICT toolkit, alongside the Rejection Block and the Mitigation Block, and it serves …"
scraped_at: "2026-07-27T15:51:35.252411+00:00"
---

# ICT Breaker Block Trading — Failed Order Block Strategy (Free PDF)

**Source:** [https://innercircletrader.net/tutorials/ict-breaker-block-trading/](https://innercircletrader.net/tutorials/ict-breaker-block-trading/)

![ICT Breaker Block diagram showing a failed order block flipping into support or resistance after liquidity sweep](https://www.innercircletrader.net/wp-content/uploads/2023/12/Supply-and-Demand-trading-strategy-1.png)

An ICT Breaker Block is a failed order block — an order block that price has broken through, which then flips and acts as support or resistance from the opposite side. It is one of three “block trio” PD Arrays in the ICT toolkit, alongside the Rejection Block and the Mitigation Block, and it serves a distinct role: it is the trigger for trend-reversal trades after a liquidity sweep.

The Breaker is what I look for when an old order block has been swept and price has shifted structure in the opposite direction. The broken OB becomes the new entry zone — same level, opposite side.

This guide is the full breakdown of the ICT Breaker Block — how to identify it, the bullish and bearish variants, the step-by-step trade flow, the difference from a regular order block, the common mistakes, and the answers to the questions I get most often.

Table of Contents

[Toggle](<#>)

#### What is an ICT Breaker Block?

A breaker block is a failed order block, identified after a liquidity sweep and a Market Structure Shift. It is one of the cleanest reversal triggers in the ICT method.

No strategy is foolproof, ICT included. Traders position at bullish order blocks with stops below the OB low, and at bearish order blocks with stops above the OB high. Sometimes the market does the opposite — it engineers liquidity, hunts those stops, and breaks the OB on the wrong side. The OB has failed.

That broken order block is now a Breaker. Price will typically retrace back to the broken zone, and that retrace is the Breaker entry.

**How to Identify a Breaker Block**

To identify a Breaker Block, I need a complete understanding of an [ICT Order Block](<https://innercircletrader.net/tutorials/ict-order-block/>) first. The Breaker is built on top of that concept.

When an order block forms against the prevailing higher-timeframe trend, the probability of that order block being violated is high — and that is exactly when a Breaker forms.

![](https://innercircletrader.net/wp-content/uploads/2024/10/ICT-Breaker-Blocks-Examples-1.png)

If price closes below the low of a bullish order block, that failed OB is a bearish Breaker, which now acts as resistance.

If price closes above the high of a bearish order block, that failed OB is a bullish Breaker, which now acts as support.

#### Types of ICT Breaker Block

Because the Breaker is derived from the order block, and order blocks come in two types, the Breaker also splits into two types.

**(I) Bullish Breaker Block**

**(II) Bearish Breaker Block**

#### ICT Bullish Breaker Block

A bullish Breaker is a failed [Bearish Order Block](<https://innercircletrader.net/tutorials/ict-bearish-order-block/>).

When price breaks a bearish order block — closing above the high of the OB — it acts as support and pushes price higher. That is a bullish Breaker.

ICT refers to the consecutive up-closed candles before the swing high (which swept liquidity, and which price later broke) as the bullish Breaker. The last up-closed candle in the sequence is the most sensitive, and for precision I typically use only that single candle as the Breaker zone.

To validate a bullish Breaker, I check four things:

  1. A clean [Liquidity Sweep](<https://innercircletrader.net/tutorials/ict-liquidity-sweep-vs-liquidity-run/>).
  2. A valid bearish order block at the swept extreme.
  3. Price closing above the high of the bearish order block.
  4. A confirming [Market Structure Shift](<https://innercircletrader.net/tutorials/ict-market-structure-shift/>) to the upside.

A real chart example is shown below.

![Bullish Breaker Block chart example — bearish order block fails, MSS to upside, price retraces to broken OB for buy entry](https://www.innercircletrader.net/wp-content/uploads/2023/12/Bullish-Breaker-block.png)

#### ICT Bearish Breaker Block

A bearish Breaker forms when a [Bullish Order Block](<https://innercircletrader.net/tutorials/ict-bullish-order-block/>) fails.

When price breaks below a bullish order block — closing below the low of the OB — it acts as resistance and pushes price lower. That is a bearish Breaker.

ICT refers to the consecutive down-closed candles before the swing low (which cleared liquidity, and which price later broke) as the bearish Breaker. The last down-closed candle is the most sensitive and is typically the only candle I use as the Breaker zone.

To validate a bearish Breaker, I check the same four conditions:

  1. A clean liquidity sweep.
  2. A valid bullish order block at the swept extreme.
  3. Price closing below the low of the bullish order block.
  4. A confirming Market Structure Shift to the downside.

![Bearish Breaker Block chart example — bullish order block fails, MSS to downside, price retraces to broken OB for sell entry](https://www.innercircletrader.net/wp-content/uploads/2023/12/Bearish-Breaker-Block.png)

![Bullish Breaker Block trade execution example — sell-side liquidity sweep, MSS, retest of broken bearish OB for buy entry](https://www.innercircletrader.net/wp-content/uploads/2023/12/trading-bullish-breaker-block.png)

![Bearish Breaker Block trade execution example — buy-side liquidity sweep, MSS, retest of broken bullish OB for sell entry](https://www.innercircletrader.net/wp-content/uploads/2023/12/trading-bearish-breaker-block.png)

#### Step-by-Step Breaker Block Trade Flow

This is the exact sequence I run on every Breaker Block setup. Save it, print it, do not skip a step.

  1. **Set the daily bias** using [ICT Daily Bias](<https://innercircletrader.net/tutorials/ict-daily-bias-trick/>). Breaker trades only work in the direction of the higher-timeframe bias.
  2. **Mark the higher-timeframe PD Array** on the daily, 4-hour, or 1-hour chart — the order block where institutions positioned.
  3. **Wait for the liquidity sweep** at the OB extreme. The sweep is the trigger event that flips the OB into a potential Breaker.
  4. **Confirm the OB has failed** — price must close past the OB extreme, not just wick through it. Body close confirms the break.
  5. **Drop to the lower timeframe** (15-minute or 5-minute) and watch for a Market Structure Shift in the new direction.
  6. **Mark the Breaker zone** — the failed order block, ideally narrowed down to the last candle in the OB sequence.
  7. **Wait for the retrace** back to the Breaker zone. Do not chase.
  8. **Execute the trade** on the Breaker tap, with stop loss beyond the swept extreme of the OB.
  9. **Take profit** at the next significant liquidity pool or the opposing extreme of the higher-timeframe range.

#### Best Time Frame to Trade the ICT Breaker Block

Breaker Blocks form on every timeframe, but the highest-probability setups are on the 1-hour and 15-minute charts when validated against a daily-timeframe PD Array.

For execution I drop to the 5-minute or 3-minute. The 1-minute is too noisy for Breaker confirmation; the 15-minute is the highest I would go for entry timing.

#### Best Pair to Trade the Breaker Block

Breaker Blocks work cleanly across markets. The strongest performance is on US index futures (NASDAQ 100 / NQ Futures and E-mini S&P 500 / ES Futures) and on the major forex pairs (GBP/USD, EUR/USD) plus Gold (XAU/USD).

For US-based futures traders, ES and NQ are CFTC-regulated futures and execute through a US futures broker (NinjaTrader, AMP, Tradovate, or a prop firm such as Topstep). TradingView is for chart analysis only.

#### Breaker Block vs Order Block

The Breaker and the Order Block are related but distinct PD Arrays.

A regular [Order Block](<https://innercircletrader.net/tutorials/ict-order-block/>) is a continuation tool. Price retraces to the OB and continues in the original direction.

A Breaker Block is a reversal tool. The OB has failed; price now retraces to the same level but trades in the opposite direction.

The visual is identical (a candle range at a swing point) but the context is opposite. An order block that has been broken is no longer a fresh order block — it is a Breaker, and the trade direction flips.

![Fresh bullish order block before being broken — continuation entry](https://innercircletrader.net/wp-content/uploads/2023/12/Bullish-order-block.png)

![Same level after price breaks below — flips into bearish Breaker, reversal entry](https://innercircletrader.net/wp-content/uploads/2023/12/Bearish-Breaker-Block-1.png)

#### Common Mistakes I See Traders Make on the Breaker Block

Five mistakes show up in nearly every Breaker Block comment thread on the site.

  1. **Trading the Breaker without a Market Structure Shift.** A liquidity sweep alone is not a Breaker. Wait for the lower-timeframe MSS in the new direction before treating the failed OB as a Breaker.
  2. **Confusing a wick break for a body break.** A wick that pierces the OB extreme is not a confirmed break. Wait for a candle body close past the extreme before marking the OB as failed.
  3. **Trading Breakers against the daily bias.** Breaker trades work in the direction of the daily bias. Counter-bias Breakers fail far more often than aligned ones.
  4. **Stop loss too tight on the Breaker zone.** Place the stop beyond the wick of the swept extreme that preceded the Breaker, with a small buffer. Stops one pip beyond the Breaker candle are routinely tagged.
  5. **Confusing the Breaker with the Mitigation Block.** A Breaker is a failed OB traded in the opposite direction. A Mitigation Block is an old OB tested again in the same direction. They look similar on the chart but represent opposite trade ideas. See the dedicated Mitigation Block guide for the full distinction.

#### FAQs About the ICT Breaker Block

**What is an ICT Breaker Block?**

An ICT Breaker Block is a failed order block — an order block that price has broken through, which then flips and acts as support or resistance from the opposite side. It is a reversal trigger after a liquidity sweep and Market Structure Shift.

**How is a Breaker Block different from an Order Block?**

An order block is a continuation tool — price retraces to it and continues. A Breaker Block is a reversal tool — the order block has failed, and price now retraces to the same level but trades in the opposite direction. Same level, opposite trade.

**What is a bullish Breaker Block?**

A bullish Breaker is a failed bearish order block. Price closed above the OB high, swept liquidity, and shifted structure to the upside. The broken OB now acts as support on the retrace.

**What is a bearish Breaker Block?**

A bearish Breaker is a failed bullish order block. Price closed below the OB low, swept liquidity, and shifted structure to the downside. The broken OB now acts as resistance on the retrace.

**What confirmation do I need for a Breaker?**

Four conditions: a liquidity sweep, a valid order block at the swept extreme, a body close past the OB extreme, and a Market Structure Shift in the new direction.

**What is the best timeframe for the Breaker Block?**

The 1-hour and 15-minute charts produce the highest-probability setups when validated against a daily PD Array. Use the 5-minute or 3-minute for execution.

**Where do I place stop loss on a Breaker trade?**

Beyond the wick of the swept extreme that preceded the Breaker, with a small buffer. Stops one pip past the Breaker candle are routinely tagged before the retrace plays out.

**Is the Breaker the same as the Mitigation Block?**

No. A Breaker is a failed OB traded in the opposite direction. A Mitigation Block is an old OB tested again in the same direction. They look similar on the chart but represent opposite trade ideas — see the dedicated Mitigation Block guide for the side-by-side.

#### ICT Breaker Block PDF Download

You can download below ICT breaker block in PDF for free. This PDF is sponsored by [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

[Download PDF](<https://ICTPULL.b-cdn.net/ICT%20PDF%204/ICT%20Breaker%20Block%20PDF%20Download.pdf>)

To learn complete ICT Trading strategy step by step, you can buy [ICT Trading PDF eBook](<http://www.ictpdf.com> "ICT Trading PDF") on [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")
