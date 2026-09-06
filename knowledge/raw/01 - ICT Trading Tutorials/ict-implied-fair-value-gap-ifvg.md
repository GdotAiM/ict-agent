---
title: "ICT Implied Fair Value Gap (IFVG) — Hidden FVG Identification with Consequent Encroachment + Free PDF"
source: "https://innercircletrader.net/tutorials/ict-implied-fair-value-gap-ifvg/"
type: "tutorial"
date: "2024-08-11T14:25:34"
modified: "2026-05-08T21:11:23"
categories:
  - "ICT Trading Tutorials"
tags:
  - "ICT IFVG"
  - "ICT Implied Fair value gap"
  - "IFVG ICT"
excerpt: "In this guide I walk you through one of the more hidden concepts in the ICT framework — the ICT Implied Fair Value Gap (IFVG). The implied FVG is not a typical visual gap; it is a hidden zone the algorithm uses to reprice and balance price delivery, marked between the consequent encroachment levels of …"
scraped_at: "2026-07-27T15:51:36.114020+00:00"
---

# ICT Implied Fair Value Gap (IFVG) — Hidden FVG Identification with Consequent Encroachment + Free PDF

**Source:** [https://innercircletrader.net/tutorials/ict-implied-fair-value-gap-ifvg/](https://innercircletrader.net/tutorials/ict-implied-fair-value-gap-ifvg/)

![ICT Implied Fair Value Gap \(IFVG\) — hidden fair value gap formed when wicks overlap the body of a large displacement candle, marked with consequent encroachment Fibonacci levels](https://innercircletrader.net/wp-content/uploads/2024/08/ICT-Liquidity-Sweep-and-Liquidity-Run_20240811_150753_0000.png)

In this guide I walk you through one of the more hidden concepts in the ICT framework — the ICT Implied Fair Value Gap (IFVG). The implied FVG is not a typical visual gap; it is a hidden zone the algorithm uses to reprice and balance price delivery, marked between the consequent encroachment levels of two overlapping wicks.

After studying this article and dedicating yourself to practice in the live market, you will be able to identify and trade the implied fair value gap (IFVG) like a pro.

**Note on naming:** the implied FVG (this article) is different from the [Inversion Fair Value Gap](<https://innercircletrader.net/tutorials/ict-inversion-fair-value-gap/>) — both are sometimes shortened to “IFVG” but they describe two distinct concepts. The implied FVG is a hidden gap inside an overlapping-wick formation. The inversion FVG is a failed FVG that has been broken and now acts as the opposite zone.

Table of Contents

[Toggle](<#>)

#### What is an ICT Implied Fair Value Gap (IFVG)?

The ICT implied fair value gap is not a typical [fair value gap](<https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/>). It is a hidden fair value gap, and the algorithm uses it to reprice and balance price delivery.

It forms when price falls or rises with a displacement move and large-bodied candles form with the wicks of the surrounding candles overlapping each other — leaving no visual fair value gap on the chart.

The “implied” gap exists between the consequent encroachment (50% midpoint) of the wick that precedes the large candle and the consequent encroachment of the wick that follows the large candle. That overlap region is the hidden gap the algorithm respects.

If you are looking for the ICT Inversion Fair Value Gap (a different concept) you can study the [ICT Inversion Fair Value Gap](<https://innercircletrader.net/tutorials/ict-inversion-fair-value-gap/>) guide.

#### How to Identify an ICT Implied Fair Value Gap

The ICT implied fair value gap is not visible to the naked eye, so instead of looking for a gap between candles, look for a displacement move with a single large-bodied candlestick and overlapping wicks on either side.

Look for a large-body candlestick whose body is overlapped by the wicks of the previous and the next candlestick — and where there is no visual gap between the wicks.

For the **(I) Bullish Implied Fair Value Gap** , identify a bullish large-bodied candlestick whose body is overlapped by the wicks of the preceding and following candlesticks.

Using the Fibonacci tool, measure the [consequent encroachment](<https://innercircletrader.net/tutorials/ict-consequent-encroachment/>) (50%) level of the upper wick of the first candle (the candlestick before the large bullish candle).

Next, use the Fibonacci tool to measure the consequent encroachment (50%) level of the lower wick of the third candle (the candlestick after the large bullish candle).

![Bullish Implied Fair Value Gap diagram — large bullish candle with the consequent encroachment of the upper wick of the first candle and the lower wick of the third candle marking the hidden gap](https://innercircletrader.net/wp-content/uploads/2024/07/BULLISH-ifvg-ict.png)

![Bullish Implied Fair Value Gap on a real chart — the area between the two CE Fibonacci levels marks the hidden FVG that price typically retests](https://innercircletrader.net/wp-content/uploads/2024/07/BULLISH-ifvg.png)

The area between these two consequent encroachment levels is identified as the Bullish Implied Fair Value Gap.

To identify a **(II) Bearish Implied Fair Value Gap** , find a large bearish candlestick whose body is overlapped by the wicks of the preceding and following candlesticks.

Use the Fibonacci tool to determine the 50% level (consequent encroachment) of the lower wick of the first candle (the candlestick before the large bearish candle).

Next, use the Fibonacci tool to find the 50% level (consequent encroachment) of the upper wick of the third candle (the candlestick after the large bearish candle).

![Bearish Implied Fair Value Gap diagram — large bearish candle with the consequent encroachment of the lower wick of the first candle and the upper wick of the third candle marking the hidden gap](https://innercircletrader.net/wp-content/uploads/2024/07/BEARISH-IMPLIED-FAIR-VALUE-GAP-ict.png)

![Bearish Implied Fair Value Gap on a real chart — the area between the two CE Fibonacci levels marks the hidden FVG that price typically retests on the way down](https://innercircletrader.net/wp-content/uploads/2024/07/BEARISG-IFVGict.png)

The area between these two consequent encroachment levels marks the Bearish Implied Fair Value Gap.

#### How to Trade an ICT Implied Fair Value Gap

To trade using an ICT implied fair value gap, follow the steps below.

**Step 1 — Determine Market Trend.** First identify the market trend of the asset — bullish or bearish. You may use the [ICT Daily Bias](<https://innercircletrader.net/tutorials/ict-daily-bias-explained/>) framework to find the trend. In a bullish trend the market makes higher highs and higher lows; in a bearish trend the market makes lower lows and lower highs.

**Step 2 — Confirmation.** If the market is in a bullish trend, wait for price to tap a higher-timeframe [PD array](<https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/>) and watch for an [ICT Market Structure Shift](<https://innercircletrader.net/tutorials/ict-market-structure-shift/>) on the lower timeframe.

**Step 3 — Identify the Large Candle.** Once you have determined the trend and price has tapped the PD array and shifted its structure, find a large candle with a large body. In a bullish trend look for a strong bullish candle with the most body range; in a bearish trend look for a large bearish candle with the most body range.

**Step 4 — Study the Preceding and Proceeding Candles.** Once you have identified one large candle, study the candle before it and the candle after it. Both of those candles should have such a structure that their wicks overlap the body of the middle candle — confirming an implied fair value gap between the consequent encroachment of the wicks of the first and third candle.

**Step 5 — Mark the Implied Fair Value Gap.** Using the Fibonacci tool, measure the consequent encroachment and mark the implied fair value gap (IFVG). When price retraces back and reprices the IFVG, you can execute your trade.

![Real market example of a bearish ICT Implied Fair Value Gap — large bearish displacement candle, hidden gap marked between the wick CE levels and price retest delivering a clean short entry](https://innercircletrader.net/wp-content/uploads/2024/07/Bearish-ICT-IFVG-example.png)

#### Step-by-Step IFVG Trade Flow (Condensed)

This is the exact sequence I run when trading an implied fair value gap.

  1. **Set the higher-timeframe trend.** Daily and H4 — bullish or bearish.
  2. **Mark the higher-timeframe PD array.** Order block, FVG or breaker that price is drawn to.
  3. **Wait for price to tap the PD array.** Confirmation that the algorithm is reaching for the level.
  4. **Drop to the lower timeframe.** 5-minute or 1-minute for the trigger.
  5. **Watch for a Market Structure Shift.** The MSS confirms the reversal at the PD array.
  6. **Spot the displacement candle.** The largest-body candle in the displacement leg after the MSS.
  7. **Verify the wick overlap.** The wicks of the candles before and after the large candle must overlap its body — leaving no visual FVG.
  8. **Mark the implied gap.** Plot the Fibonacci tool on each surrounding wick and mark the 50% (CE) of each. The area between the two CE lines is the IFVG.
  9. **Wait for the retest.** Price must retrace back into the IFVG zone.
  10. **Enter at the CE retest.** Buy the bullish IFVG retest, sell the bearish IFVG retest.
  11. **Set the stop.** Beyond the opposite edge of the IFVG, or beyond the displacement candle’s high/low for tighter stops.
  12. **Take profit at the next draw on liquidity.** Old high/low, relative equal level or higher-timeframe FVG.

#### IFVG vs Regular FVG vs Inversion FVG

The three FVG concepts confuse a lot of traders. Here is the quick differentiator.

  * **Regular FVG** — visible 3-candle gap where the wicks of the 1st and 3rd candle do NOT overlap (covered in the [Fair Value Gap](<https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/>) guide).
  * **Implied FVG (this article)** — hidden gap inside a 3-candle displacement where the wicks of the 1st and 3rd candle DO overlap the body of the middle candle. Marked between the CE of the surrounding wicks.
  * **Inversion FVG** — a regular FVG that has been broken and now acts as the opposite zone (a failed FVG). Covered in the [Inversion Fair Value Gap](<https://innercircletrader.net/tutorials/ict-inversion-fair-value-gap/>) guide.

The three concepts are commonly grouped under the umbrella term “IFVG” but only two of them legitimately abbreviate to that — the implied FVG and the inversion FVG. The regular FVG is just FVG (or BISI/SIBI for the directional variants).

#### Best Markets for Trading the Implied FVG

The implied FVG works on every market that the ICT methodology is applied to — but the cleanest signatures print on instruments that produce strong displacement moves.

  * **NQ (NASDAQ futures)** and **ES (S &P 500 futures)** — large displacement candles around the New York open and the 09:50 NY-AM macro produce the cleanest implied FVGs.
  * **XAU/USD (Gold)** — gold’s reaction to 08:30 ET news releases routinely creates large-body candles with overlapping surrounding wicks.
  * **GBP/USD** and **EUR/USD** — London-killzone displacement legs frequently leave implied FVGs for the NY-AM retest.

**For traders in the United States** who follow the CFTC FIFO and no-hedge rules, NQ and ES on the 1-minute and 5-minute charts are the most natural fit for the implied FVG. The 09:50 NY-AM [macro window](<https://innercircletrader.net/tutorials/ict-macro-time-based-strategy/>) often produces the displacement candle whose hidden gap delivers the entry on the retest later in the session.

#### Common Mistakes Around the Implied FVG

These are the recurring mistakes I see when traders first start trading the implied FVG.

  1. **Marking the wrong wicks.** The CE must be measured on the upper wick of the FIRST candle and the lower wick of the THIRD candle (for bullish IFVG). The reverse for bearish. Reversing the wicks inverts the entire zone.
  2. **Confusing IFVG with regular FVG.** If a visual gap exists between the 1st and 3rd candle wicks, it is a regular FVG — not an implied FVG. The implied FVG is the variant where the wicks overlap.
  3. **Confusing implied with inversion.** Both shorten to “IFVG” but they are different concepts. Implied = hidden gap inside an overlap. Inversion = failed FVG that flipped roles.
  4. **Trading without HTF context.** The implied FVG is most reliable when it sits at a higher-timeframe PD array and is preceded by a lower-timeframe MSS. Standalone IFVGs in the middle of a range deliver poorly.
  5. **Stop too tight.** Stops parked at the CE often get hunted on the second test. The opposite edge of the IFVG is the conservative stop.
  6. **Ignoring news.** The displacement candle that creates an implied FVG is often the news-driven candle itself. Trading the IFVG retest before the news settles can produce false signals.

#### ICT Implied Fair Value Gap IFVG PDF Download

You can download below ICT implied fair value gap IFVG in PDF for free. This PDF is sponsored by [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

[Download PDF](<https://ICTPULL.b-cdn.net/PDF%20Download/ICT%20Implied%20Fair%20value%20Gap%20%E2%80%93%20IFVG%20PDF%20Download.pdf>)

To learn the complete ICT Trading strategy step by step, you can buy the [ICT Trading PDF eBook](<http://www.ictpdf.com> "ICT Trading PDF") on [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

#### FAQs about the ICT Implied Fair Value Gap

Brief answers to the questions readers ask most often about the implied FVG.

**What is an implied fair value gap?**

An implied fair value gap (implied FVG or IFVG) is a hidden gap formed inside a displacement leg where a large-bodied candle has its body overlapped by the wicks of the preceding and following candles — leaving no visual gap on the chart. The hidden gap is marked between the consequent encroachment (50%) of the surrounding wicks.

**What is the difference between implied FVG and regular FVG?**

A regular FVG is visible — there is a clean gap between the 1st and 3rd candle wicks. An implied FVG is hidden — the wicks of the 1st and 3rd candles overlap the body of the middle (large) candle, so no visual gap appears.

**What is the difference between implied FVG and inversion FVG?**

Both abbreviate to “IFVG” but they are different concepts. Implied FVG is a hidden gap inside an overlapping-wick displacement. Inversion FVG is a failed regular FVG that has been broken and now acts as the opposite zone (a flipped role).

**How do I find an implied FVG?**

Look for a large-bodied displacement candle. Verify that the wicks of the preceding and following candles overlap the body of the large candle. Mark the consequent encroachment (50%) of each surrounding wick — the area between is the implied FVG.

**Where do I enter an implied FVG trade?**

After a higher-timeframe PD-array tap and a lower-timeframe MSS, wait for price to retrace back into the implied FVG. Enter at the CE retest of the IFVG zone — buy a bullish IFVG and sell a bearish IFVG.

**Where do I place the stop loss on an implied FVG trade?**

The conservative stop sits beyond the opposite edge of the implied FVG. Tighter stops can sit beyond the displacement candle’s high or low.

**Where do I take profit?**

The next draw-on-liquidity in the trade direction — typically a relative equal high/low, the prior session high/low or an unfilled higher-timeframe FVG.

**What timeframe is best for the implied FVG?**

The 15-minute and 5-minute produce the cleanest implied FVGs around the NY-AM session. The 1-minute is used to time the entry on the retest.

**Does the implied FVG work on indices and gold?**

Yes — NQ, ES and XAU/USD produce textbook implied FVGs around the 08:30 ET news releases and the 09:50 NY-AM macro window.

**What is consequent encroachment in this context?**

Consequent encroachment is the 50% midpoint of any wick or PD array. For the implied FVG, the CE of each surrounding wick is what defines the hidden gap zone. Read the full [consequent encroachment guide](<https://innercircletrader.net/tutorials/ict-consequent-encroachment/>).

**Why is the implied FVG called “hidden”?**

Because it is not visible on the chart at first glance — there is no gap between the candle wicks. The gap is “implied” by the consequent encroachment of the wicks, which is why the algorithm respects it even though traders without the framework cannot see it.
