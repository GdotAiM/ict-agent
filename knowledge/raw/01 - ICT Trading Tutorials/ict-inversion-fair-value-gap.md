---
title: "ICT Inverse Fair Value Gap (IFVG) — Inversion FVG Setup with Examples + Free PDF"
source: "https://innercircletrader.net/tutorials/ict-inversion-fair-value-gap/"
type: "tutorial"
date: "2024-04-12T16:25:49"
modified: "2026-05-07T21:17:07"
categories:
  - "ICT Trading Tutorials"
tags:
  - "ICT inversion fair value gap"
  - "inverse FVG"
  - "inversion fair value gap"
  - "inversion FVG"
excerpt: "The ICT Inverse Fair Value Gap — also called the Inversion Fair Value Gap or IFVG — is a mitigated Fair Value Gap that failed to hold price. Instead of throwing the broken FVG away, ICT uses it in the opposite direction. A bearish FVG that gets violated becomes a bullish IFVG. A bullish FVG …"
scraped_at: "2026-07-27T15:51:38.075021+00:00"
---

# ICT Inverse Fair Value Gap (IFVG) — Inversion FVG Setup with Examples + Free PDF

**Source:** [https://innercircletrader.net/tutorials/ict-inversion-fair-value-gap/](https://innercircletrader.net/tutorials/ict-inversion-fair-value-gap/)

![ICT Inverse Fair Value Gap \(IFVG\) diagram showing a violated fair value gap acting as reversal support or resistance](https://innercircletrader.net/wp-content/uploads/2024/04/Inverse-fair-value-gap.png)

The ICT Inverse Fair Value Gap — also called the Inversion Fair Value Gap or IFVG — is a mitigated [Fair Value Gap](<https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/>) that failed to hold price. Instead of throwing the broken FVG away, ICT uses it in the opposite direction. A bearish FVG that gets violated becomes a bullish IFVG. A bullish FVG that gets violated becomes a bearish IFVG.

A broken FVG is not trash — it is one of the institutional [PD Arrays](<https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/>) in the ICT toolkit, just inverted. The IFVG signals the earliest shift in momentum on the lower timeframe, which makes it a high-precision trigger for the next directional leg.

This guide is the full breakdown of the ICT Inverse Fair Value Gap — what it is, how to identify it, the bullish and bearish variants, the three conditions that make an IFVG most reliable, the step-by-step trade flow, the common mistakes I see traders make, and the answers to the questions I get most often.

Table of Contents

[Toggle](<#>)

#### What is a Fair Value Gap?

The ICT Fair Value Gap is a three-candle structure with a gap between the high and low of candle 1 and candle 3. The gap represents an institutional imbalance — delivery was one-sided enough that buy and sell orders did not overlap during the move.

![ICT Fair Value Gap diagram showing the three-candle imbalance with unfilled gap between candle 1 and candle 3](https://innercircletrader.net/wp-content/uploads/2024/04/ICT-Fair-Value-Gap-1.png)

For the full FVG breakdown — strength tiers, identification rules, and trade flow — see the [ICT Fair Value Gap](<https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/>) guide.

#### What is the ICT Inverse Fair Value Gap?

The ICT Inverse Fair Value Gap is a failed fair value gap — one that price did not respect. An IFVG forms when price closes beyond a fair value gap, breaking it in the direction opposite to its original delivery.

The IFVG signals the earliest shift in momentum. While price moves in a direction, it respects the fair value gaps and continues in that direction. But the moment a fair value gap is violated, that broken gap becomes the IFVG and signals the first momentum shift, which can lead to a short retracement or a full directional change.

![ICT Inverse Fair Value Gap example chart — bearish FVG violated by bullish close, becomes bullish IFVG support](https://innercircletrader.net/wp-content/uploads/2024/04/ICT-Inverse-Fair-Value-Gap.png)

#### How to Identify the ICT Inverse Fair Value Gap

To identify an IFVG, work in two steps:

  1. Identify a regular fair value gap on the chart — a 3-candle imbalance with a clear unfilled gap between candle 1 and candle 3.
  2. Watch for price to close beyond the FVG in the opposite direction — a candle body close that violates the fair value gap.

When the FVG is broken by a body close, mark it as an IFVG and treat it as a PD Array in the opposite direction. The original bearish FVG flips to a bullish IFVG; the original bullish FVG flips to a bearish IFVG.

The body close is the critical diagnostic. A wick that pierces the FVG is not enough — it must be a clean candle body close past the gap to qualify as an inversion.

#### Types of IFVG

Because fair value gaps come in two types, the IFVG also splits into two — bullish and bearish — each with its own setup criteria.

#### (I) Bullish Inverse Fair Value Gap

A bullish IFVG is a bearish fair value gap that has been violated by price closing above it.

The sequence: identify a bearish FVG. Watch for price to close above the bearish FVG. The moment it closes above, that bearish FVG flips into a bullish IFVG. It now acts as support, and the next retest of the level is a buy entry.

The bullish IFVG signals losing strength on the seller side and an initial momentum shift toward the buy-side.

![Bullish ICT Inverse Fair Value Gap example — original bearish FVG violated by bullish close, retest as buy entry](https://innercircletrader.net/wp-content/uploads/2024/04/inverse-FVG.png)

#### (II) Bearish Inverse Fair Value Gap

A bearish IFVG is a bullish fair value gap that has been violated by price closing below it.

The sequence: identify a bullish FVG. Watch for price to close below the bullish FVG. The moment it closes below, that bullish FVG flips into a bearish IFVG. It now acts as resistance, and the next retest of the level is a sell entry.

The bearish IFVG signals losing strength on the buyer side and an initial momentum shift toward the sell-side.

![Bearish ICT Inverse Fair Value Gap example — original bullish FVG violated by bearish close, retest as sell entry](https://innercircletrader.net/wp-content/uploads/2024/04/inversion-FVG.png)

#### How to Trade the ICT Inverse Fair Value Gap

ICT IFVGs are most reliable in three specific conditions.

**(I) IFVG Formed in the Premium Zone.** When price is trading in the premium zone (above equilibrium), traders are looking to sell at the fair value gap. But if price violates the FVG by closing above it, the FVG flips to a bullish IFVG. Buy at the consequent encroachment of the IFVG with stop loss below the inversion FVG. See the [Consequent Encroachment](<https://innercircletrader.net/tutorials/ict-consequent-encroachment/> "Consequent Encroachment") guide for the precise entry level inside the IFVG.

**(II) IFVG Formed in the Discount Zone.** When price is trading in the discount zone (below equilibrium), traders are looking to buy at the fair value gap. But if price violates the FVG by closing below it, the FVG flips to a bearish IFVG. Sell at the consequent encroachment of the IFVG with stop loss above the inversion FVG.

**(III) IFVG Formed After a Failed Market Structure Shift.** When price is in a higher-timeframe PD Array and shifts its structure on the lower timeframe, traders typically look to buy or sell at the FVG after the [MSS](<https://innercircletrader.net/tutorials/ict-market-structure-shift/> "Market Structure Shift"). But sometimes price does not stop at the fair value gap — it sweeps the liquidity of the previous high or low, staying inside the higher-timeframe PD Array. Watch for the IFVG that forms after this failed MSS to execute a trade in the original higher-timeframe direction.

#### Step-by-Step IFVG Trade Flow

This is the exact sequence I run on every IFVG setup. Save it, print it, do not skip a step.

  1. **Set the daily bias** using [ICT Daily Bias](<https://innercircletrader.net/tutorials/ict-daily-bias-explained/>). IFVG trades work cleanest in the direction of the higher-timeframe bias.
  2. **Identify the original fair value gap** on the chart timeframe you are working with — typically the 15-minute or 5-minute for execution.
  3. **Watch for violation** — a candle body close past the FVG in the opposite direction. A wick poke is not enough.
  4. **Confirm the violation context** — is the IFVG forming in the premium zone, discount zone, or after a failed MSS? These are the three reliable conditions. Outside them, the IFVG is a coin flip.
  5. **Mark the IFVG zone** — the original FVG body is now the IFVG. Mark its high and low; the consequent encroachment (50% level) is the precise entry.
  6. **Wait for the retest** back to the IFVG. Do not chase the violation candle.
  7. **Execute the trade** at the consequent encroachment of the IFVG, with stop loss beyond the IFVG extreme — below the IFVG low for bullish, above the IFVG high for bearish.
  8. **Take profit** at the next significant draw on liquidity in the trade direction — old highs, old lows, or higher-timeframe PD Array.

#### Best Time Frame to Spot the ICT IFVG

The IFVG serves two distinct purposes, and the timeframe depends on the use case.

For **daily bias identification** , use the higher timeframes — 1-day or 4-hour. An IFVG on the daily chart signals a meaningful momentum shift on the dominant trend.

For **trade entry execution** , drop to the lower timeframes — 15-minute, 5-minute, or 3-minute. The IFVG at this resolution gives precise entry timing inside a higher-timeframe PD Array tap.

#### Best Pair for ICT IFVG Trading

ICT introduced the IFVG concept on US index futures — **NASDAQ 100 (NQ Futures)** and the **E-mini S &P 500 (ES Futures)**. These remain the cleanest instruments for the model because the time-of-day delivery on US index futures is the most predictable.

The IFVG also works well on the major forex pairs and metals: **GBP/USD** , **EUR/USD** , and **XAU/USD** (Gold) all respect the same inversion mechanics.

For US-based futures traders, ES and NQ are CFTC-regulated futures and execute through a US futures broker (NinjaTrader, AMP, Tradovate, or a prop firm such as Topstep). TradingView is for chart analysis only.

#### Common Mistakes I See Traders Make on the IFVG

Five mistakes account for the majority of failed IFVG trades I see in the comments. Avoid these and the model converts at a much higher rate.

  1. **Acting on a wick violation instead of a body close.** A wick that pierces the FVG is not an IFVG. The candle body must close past the FVG in the opposite direction. Wait for the close.
  2. **Trading IFVGs outside the three reliable conditions.** The IFVG works best in the premium zone, the discount zone, or after a failed MSS. Random IFVGs in the middle of trending price without context are coin flips.
  3. **Trading IFVGs against the daily bias.** Counter-bias IFVGs fail far more often than aligned IFVGs. Filter every setup through the daily bias before acting.
  4. **Stop loss inside the IFVG zone.** Place the stop beyond the IFVG extreme, with a small buffer. Stops one pip past the IFVG get tagged routinely on the typical re-test spike.
  5. **Confusing the IFVG with a regular FVG.** The original FVG and the IFVG are at the same price but operate in opposite directions. Mark which is which clearly. Trading the IFVG as if it were still the original FVG inverts your trade direction.

#### FAQs About the ICT Inverse Fair Value Gap

**What is the ICT Inverse Fair Value Gap (IFVG)?**

The IFVG is a fair value gap that has been violated by price. A bearish FVG that price closes above becomes a bullish IFVG. A bullish FVG that price closes below becomes a bearish IFVG. The broken gap now acts as support or resistance from the opposite direction.

**How is an IFVG different from a regular FVG?**

A regular FVG is an unfilled imbalance that price returns to and rebalances in the direction of the displacement leg. An IFVG is the same FVG after it has been violated — broken by a body close past the gap, signalling a momentum shift in the opposite direction.

**What is a bullish IFVG?**

A bullish IFVG forms when price closes above a bearish fair value gap. The original bearish FVG flips to act as support, and the retest is the buy entry. It signals the seller side losing strength.

**What is a bearish IFVG?**

A bearish IFVG forms when price closes below a bullish fair value gap. The original bullish FVG flips to act as resistance, and the retest is the sell entry. It signals the buyer side losing strength.

**When is an IFVG most reliable?**

Three conditions: when the IFVG forms in the premium zone for short setups, when it forms in the discount zone for long setups, or when it forms after a failed Market Structure Shift inside a higher-timeframe PD Array.

**How do I confirm an IFVG?**

Body close past the original FVG in the opposite direction. A wick that pierces the FVG is not enough — wait for a candle body close to validate the inversion.

**Where do I place stop loss on an IFVG trade?**

Beyond the IFVG extreme, with a small buffer — below the IFVG low for bullish trades, above the IFVG high for bearish trades. Stops inside the IFVG zone get tagged on the re-test spike.

**What is the best timeframe for the IFVG?**

Daily for momentum-shift identification on the dominant trend. 15-minute, 5-minute, or 3-minute for trade entry execution. The two timeframes serve different roles inside the same model.

**What instruments work best for the IFVG?**

US index futures (NASDAQ 100 / NQ and E-mini S&P 500 / ES) produce the cleanest IFVG setups. Major forex pairs (GBP/USD, EUR/USD) and Gold (XAU/USD) also respect the same inversion mechanics.

#### ICT Inversion Fair Value Gap PDF Download

You can download below ICT inversion fair value gap in PDF for free. This PDF is sponsored by [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

[Download PDF](<https://ICTPULL.b-cdn.net/ICT%20PDF%203/ICT%20Inversion%20Fair%20Value%20Gap%20PDF%20Download.pdf>)

To learn complete ICT Trading strategy step by step, you can buy [ICT Trading PDF eBook](<http://www.ictpdf.com> "ICT Trading PDF") on [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")
