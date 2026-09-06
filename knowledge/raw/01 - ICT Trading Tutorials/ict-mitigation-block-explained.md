---
title: "ICT Mitigation Block Explained — Continuation Setup vs Breaker Block (Free PDF)"
source: "https://innercircletrader.net/tutorials/ict-mitigation-block-explained/"
type: "tutorial"
date: "2024-12-09T05:18:11"
modified: "2026-05-06T22:24:50"
categories:
  - "ICT Trading Tutorials"
tags:
  - "ICT mitigation block"
  - "mitigation block"
  - "mitigation block forex"
  - "mitigation block ICT"
excerpt: "An ICT Mitigation Block is an old order block that gets re-tested by price after the original move played out, and that re-test acts as continuation support or resistance in the same direction as the original move. It is one of the institutional PD Arrays in the ICT toolkit — the third member of the …"
scraped_at: "2026-07-27T15:51:34.394492+00:00"
---

# ICT Mitigation Block Explained — Continuation Setup vs Breaker Block (Free PDF)

**Source:** [https://innercircletrader.net/tutorials/ict-mitigation-block-explained/](https://innercircletrader.net/tutorials/ict-mitigation-block-explained/)

![ICT Mitigation Block diagram showing an old order block re-tested as continuation support or resistance](https://innercircletrader.net/wp-content/uploads/2024/05/ICT-Mitigation-Block-Explained-in-Depth-1.png)

An ICT Mitigation Block is an old order block that gets re-tested by price after the original move played out, and that re-test acts as continuation support or resistance in the same direction as the original move. It is one of the institutional [PD Arrays](<https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/>) in the ICT toolkit — the third member of the “block trio” alongside the Breaker Block and the Rejection Block — and it has a distinct role within that family: the Mitigation is a continuation tool, not a reversal tool.

The mechanism is simple: when smart money built a position at the original order block and rode the move, some of that institutional order remained partially unfilled. When price returns to the same OB level later, those resting orders get mitigated — completed — and the OB delivers the next leg in the original direction.

This guide is the full breakdown of the ICT Mitigation Block — what it is, how to identify it, the bullish and bearish variants, the trade flow, the key difference from the Breaker Block, the common mistakes, and the answers to the questions I get most often.

Table of Contents

[Toggle](<#>)

#### What is the ICT Mitigation Block?

The Mitigation Block is an old, partially-mitigated order block that gets re-tested by price after the initial displacement leg has played out. The retest is the entry; the trade direction is the same as the original OB direction.

The “mitigation” in the name refers to the unfilled portion of the original institutional order. When price returns to the OB, those orders get filled — mitigated — and price continues in the original direction.

Think of it as an order block getting a second chance. The OB delivered once; some of the institutional fill was incomplete; now price comes back to finish the job.

#### How to Identify an ICT Mitigation Block

To identify a Mitigation Block, I need three conditions in sequence:

  1. A valid [Order Block](<https://innercircletrader.net/tutorials/ict-order-block/>) on a higher timeframe.
  2. A clear displacement leg from that OB in the direction of the daily bias.
  3. A retracement back to the OB zone after the leg has extended.

Critically: the OB body must NOT be broken on the retrace. If price closes past the OB extreme, the OB has failed — that is a Breaker Block, not a Mitigation. The Mitigation requires the OB to hold on the retest.

![ICT Mitigation Block identification chart — old order block holds on retrace, price continues in original direction](https://innercircletrader.net/wp-content/uploads/2024/05/Mitigation-Block-ICT.png)

#### Bearish ICT Mitigation Block

A bearish Mitigation Block forms in a downtrend. The original bearish order block delivered the first leg lower, price made a new low, and then retraced back upward toward the OB zone.

When the retrace reaches the bearish OB and price reacts (lower-timeframe Market Structure Shift down, rejection candle, or CISD), that is the Mitigation entry. The trade is sell, in line with the original OB direction.

The stop loss sits above the high of the bearish OB candle, with a small buffer.

![Bearish ICT Mitigation Block diagram — old bearish order block holds on retrace in a downtrend](https://innercircletrader.net/wp-content/uploads/2024/05/ICT-bearish-mitigation-block.png)

![Bearish ICT Mitigation Block live chart example — sell entry at OB tap with stop above OB high](https://innercircletrader.net/wp-content/uploads/2024/05/bearish-mitigation-block-1.png)

#### Bullish ICT Mitigation Block

A bullish Mitigation Block forms in an uptrend. The original bullish order block delivered the first leg higher, price made a new high, and then retraced back downward toward the OB zone.

When the retrace reaches the bullish OB and price reacts (lower-timeframe Market Structure Shift up, rejection candle, or CISD), that is the Mitigation entry. The trade is buy, in line with the original OB direction.

The stop loss sits below the low of the bullish OB candle, with a small buffer.

![Bullish ICT Mitigation Block diagram — old bullish order block holds on retrace in an uptrend](https://innercircletrader.net/wp-content/uploads/2024/05/ICT-bullish-mitigation-block.png)

![Bullish ICT Mitigation Block live chart example — buy entry at OB tap with stop below OB low](https://innercircletrader.net/wp-content/uploads/2024/05/bullish-mitigation-block.png)

#### Step-by-Step Mitigation Block Trade Flow

This is the exact sequence I run on every Mitigation Block setup. Save it, print it, do not skip a step.

  1. **Set the daily bias** using [ICT Daily Bias](<https://innercircletrader.net/tutorials/ict-daily-bias-trick/>). Mitigation Block trades only work in the direction of the higher-timeframe trend.
  2. **Identify the original order block** on the daily, 4-hour, or 1-hour chart. The OB must have already delivered a clean displacement leg in the trend direction.
  3. **Confirm the OB has NOT been broken** by any subsequent price action. Body close past the OB extreme disqualifies it (that is a Breaker, not a Mitigation).
  4. **Wait for the retrace** back to the OB zone. Do not pre-position.
  5. **Drop to a lower timeframe** (5-minute or 3-minute) at the OB tap and watch for a confirmation — Market Structure Shift, CISD, or rejection candle in the direction of the original trend.
  6. **Mark the Mitigation zone** — the body of the OB candle, narrowed to the most relevant single candle if the OB spans multiple bars.
  7. **Execute the trade** on the OB tap with stop loss beyond the OB extreme (above the high for bearish, below the low for bullish), with a small buffer.
  8. **Take profit** at the next significant draw on liquidity in the direction of the trend, or at the prior swing extreme.

#### ICT Mitigation Block vs ICT Breaker Block

The Mitigation Block and the Breaker Block are the most commonly confused pair in the ICT toolkit. Both involve an old order block being re-tested. The difference is everything.

**The Breaker Block.** The original OB has failed — price closed past the OB extreme, swept liquidity beyond it, and shifted structure in the OPPOSITE direction. The retrace to the broken OB now trades against the original OB direction.

**The Mitigation Block.** The original OB has held — price did NOT close past the OB extreme. The retrace tests the OB but respects it, and the trade continues in the SAME direction as the original OB.

Same level on the chart. Opposite trade idea. The body close past the extreme is the single most important diagnostic — that is what separates a Breaker from a Mitigation.

![ICT Mitigation Block vs Breaker Block side-by-side comparison chart](https://innercircletrader.net/wp-content/uploads/2024/05/Mitigation-Block-vs-Breaker-Block.png)

#### XAU/USD Mitigation Block Example

Below is a worked example of a Mitigation Block on XAU/USD (Gold).

![XAU/USD Gold Mitigation Block trade example — old order block holds on retrace, entry delivers in original direction](https://innercircletrader.net/wp-content/uploads/2024/05/mitigation-block-example.png)

In the chart above, the bearish OB on the 1-hour timeframe delivered the first leg lower. Price made a new low, then retraced back to the OB zone. The OB held — no body close past the OB high — and a 5-minute MSS to the downside confirmed the Mitigation entry.

The sell trade was executed at the OB tap with stop loss above the OB high. Take profit targeted the next swing low. The setup delivered a clean 1:3 risk-reward.

#### Common Mistakes I See Traders Make on the Mitigation Block

Five mistakes show up in nearly every Mitigation Block comment thread.

  1. **Confusing the Mitigation with the Breaker.** The body-close test is the single diagnostic. If price closed past the OB extreme, it is a Breaker (reversal trade). If the OB held, it is a Mitigation (continuation trade). Get this wrong and the trade direction inverts.
  2. **Trading Mitigations against the daily bias.** Mitigations are continuation trades. They only work when the original OB direction matches the higher-timeframe bias. Counter-bias Mitigations fail far more often than aligned ones.
  3. **Entering before the OB confirms the hold.** Wait for the lower-timeframe MSS or CISD in the original trend direction. A simple wick into the OB without confirmation is not enough.
  4. **Stop loss too tight on the OB extreme.** Place the stop with a small buffer beyond the OB extreme. Stops one pip past the OB get tagged routinely on the retest spike.
  5. **Forcing the Mitigation in choppy or counter-trend conditions.** The Mitigation is a continuation tool. In sideways or counter-trending markets, the OB direction loses its institutional context and the setup becomes a coin flip.

#### FAQs About the ICT Mitigation Block

**What is an ICT Mitigation Block?**

An ICT Mitigation Block is an old order block that gets re-tested by price after the initial move has played out. The retest acts as continuation support or resistance in the same direction as the original OB. The trade is in line with the original OB, not against it.

**How is a Mitigation Block different from a regular Order Block?**

A regular order block is a fresh, untested institutional zone. A Mitigation Block is an old order block that has already delivered one move and is being tested again. Both produce continuation trades; the Mitigation is the second-chance entry.

**How is a Mitigation Block different from a Breaker Block?**

The body close test. In a Breaker, price closed past the OB extreme — the OB failed and the trade flips direction. In a Mitigation, the OB held — the trade continues in the original OB direction. Same level on the chart, opposite trade idea.

**What is a bullish Mitigation Block?**

A bullish Mitigation Block is an old bullish order block in an uptrend that holds on retrace. The trade is buy at the OB tap with stop below the OB low, target at the next draw on liquidity above.

**What is a bearish Mitigation Block?**

A bearish Mitigation Block is an old bearish order block in a downtrend that holds on retrace. The trade is sell at the OB tap with stop above the OB high, target at the next draw on liquidity below.

**Where do I place stop loss on a Mitigation trade?**

Beyond the OB extreme — above the high for bearish, below the low for bullish — with a small buffer. Stops one pip past the OB get tagged on the spike that often precedes the real reaction.

**What confirmation do I need for a Mitigation Block?**

A lower-timeframe Market Structure Shift, CISD, or clean rejection candle in the direction of the original trend, after price taps the OB and respects it.

**What is the best timeframe for the Mitigation Block?**

1-hour and 4-hour for identification when validated against a daily bias. The 5-minute or 3-minute for entry timing on the retest.

#### ICT Mitigation Block PDF Download

You can download below ICT mitigation block in PDF for free. This PDF is sponsored by [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

[Download PDF](<https://ICTPULL.b-cdn.net/ICT%20PDF%202/ICT%20Mitigation%20Block%20PDF%20Download.pdf>)

To learn complete ICT Trading strategy step by step, you can buy [ICT Trading PDF eBook](<http://www.ictpdf.com> "ICT Trading PDF") on [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")
