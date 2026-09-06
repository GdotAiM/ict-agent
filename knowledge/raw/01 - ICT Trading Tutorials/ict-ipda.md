---
title: "ICT IPDA — Interbank Price Delivery Algorithm Explained (20/40/60-Day Cycles + Free PDF)"
source: "https://innercircletrader.net/tutorials/ict-ipda/"
type: "tutorial"
date: "2024-03-21T15:54:37"
modified: "2026-05-07T21:04:03"
categories:
  - "ICT Trading Tutorials"
tags:
  - "algo trading"
  - "ICT IPDA"
  - "inter bank price delivery algorithm"
  - "IPDA"
excerpt: "IPDA stands for Interbank Price Delivery Algorithm — the algorithmic system Michael Huddleston taught for understanding how price moves in the forex and futures markets. The IPDA is the framework ICT uses to explain why markets are not random: every move serves either to balance an imbalance or to take liquidity, and the algorithm follows …"
scraped_at: "2026-07-27T15:51:38.571090+00:00"
---

# ICT IPDA — Interbank Price Delivery Algorithm Explained (20/40/60-Day Cycles + Free PDF)

**Source:** [https://innercircletrader.net/tutorials/ict-ipda/](https://innercircletrader.net/tutorials/ict-ipda/)

![ICT IPDA Interbank Price Delivery Algorithm diagram showing 20-day, 40-day, and 60-day cycles](https://innercircletrader.net/wp-content/uploads/2024/03/ict-IPDA.png)

IPDA stands for Interbank Price Delivery Algorithm — the algorithmic system Michael Huddleston taught for understanding how price moves in the forex and futures markets. The IPDA is the framework ICT uses to explain why markets are not random: every move serves either to balance an imbalance or to take liquidity, and the algorithm follows specific cycles tied to the 20-, 40-, and 60-day lookback ranges.

Price you see on the live chart is not random. It follows the IPDA’s rules. Once I understand those rules, the chart stops looking like noise and starts looking like a sequence of liquidity raids and imbalance rebalances on a predictable schedule.

This guide is the full breakdown of ICT IPDA — what it is, how it works, the quarterly shifts, the 20/40/60-day cycles, the step-by-step trade flow for IPDA-driven setups, the common mistakes I see traders make, and the answers to the questions I get most often.

Table of Contents

[Toggle](<#>)

#### What is IPDA in ICT Trading?

IPDA stands for Interbank Price Delivery Algorithm. The word “algorithm” simply means a defined set of rules used to complete a task. Applied to forex, IPDA is the set of rules that institutions follow to deliver price across currency pairs, indices, and metals.

In this age of technology, anything online is governed by rules. YouTube has its recommendation algorithm. Google has its search algorithm. Forex price delivery is no different — there is an institutional algorithm controlling the moves you see, and that algorithm is the IPDA.

The IPDA is used to calculate the highs and lows of the past 20-day, 40-day, and 60-day ranges for liquidity-targeting purposes. Those previous-period extremes are where institutional buy stops and sell stops cluster — and the IPDA targets them on a predictable schedule.

#### How IPDA Works

The IPDA’s price delivery is not random. It has two clear objectives — and every meaningful move on the chart is one of them in motion.

**(I) Balance an imbalance.** When delivery has been one-sided, price returns to rebalance the gap. Imbalance shows up on the chart as a fair value gap — three candles where the high of candle 1 and the low of candle 3 do not overlap, leaving an unfilled price range in the middle.

**(II) Hunt liquidity.** Markets need active counterparties — willing buyers for sellers and willing sellers for buyers. Liquidity sits at the swing extremes (old highs, old lows) where retail traders place their stops. The IPDA targets these clusters because they are where the institutional fuel is.

Whether the IPDA is balancing an imbalance or hunting liquidity on any given day depends on the daily bias. Mark the previous day’s, week’s, and month’s highs and lows because these are the most important liquidity zones on the chart — buy stops cluster above old highs, sell stops cluster below old lows. The IPDA may target any of these to fuel the next leg.

If the bias supports rebalancing rather than liquidity hunting, mark the [SIBI and BISI](<https://innercircletrader.net/tutorials/sibi-and-bisi-the-ict-concepts/> "SIBI and BISI") imbalances and wait for price to react at those levels.

![IPDA price delivery example chart — price hunts old low liquidity, then rallies up to hunt old high liquidity, balancing imbalance along the way](https://innercircletrader.net/wp-content/uploads/2024/03/IPDA.png)

In the picture above, price hunts the liquidity below the old low, then rallies up to hunt the liquidity above the old high — and along the way it balances the imbalance left in between. None of this is random. The IPDA is delivering price along its predefined route.

#### IPDA Quarterly Shifts

A foundational step in mastering IPDA is recognising the higher-timeframe quarterly shifts. These shifts occur every 3 to 4 months — the market typically resets and changes direction on this cycle.

![ICT IPDA quarterly shifts example — EUR/USD changing direction every 3 to 4 months on the daily chart](https://innercircletrader.net/wp-content/uploads/2024/03/ICT-IPDA-quarterly-cycles.png)

In the EUR/USD chart above, price changes direction every 3 to 4 months — a process called the IPDA quarterly shift. Markets do not move in one direction all year because market makers (the institutions running the IPDA) deliberately influence these changes to take liquidity at both ends of the longer cycle.

Inside each quarterly shift, price rotation alternates between External Range Liquidity and [Internal Range Liquidity](<https://innercircletrader.net/tutorials/ict-internal-external-liquidity/>). ERL is the swing highs and lows of the dealing range; IRL is the fair value gaps inside the range. Reading where in the rotation the chart sits is the key to anticipating the IPDA’s next move.

#### IPDA 20, 40, 60-Day Cycles

Inside each quarterly shift, the IPDA cycles through three nested lookback ranges — 20 days, 40 days, and 60 days. Each range marks a level the algorithm uses for institutional reference.

![ICT IPDA 20, 40, 60-day cycles chart showing previous 20-, 40-, and 60-day highs and lows on the daily timeframe](https://innercircletrader.net/wp-content/uploads/2024/03/ICT-IPDA-20-40-60-days-cycle.png)

The picture above shows the highs and lows of the past 20, 40, and 60 days. The market establishes a 40-day high before shifting to a bearish trend, ultimately forming new 60-day highs and lows. Once liquidity is taken from the 60-day high, the market seeks to capture the 60-day low.

This behaviour aligns with the IPDA logic: the market is programmed to target both the highs and lows of the previous 20, 40, and 60 days within each quarterly cycle. After every 20-day stretch, a shift typically prints on the daily chart — the IPDA lookback period reset that ICT himself emphasised. Roughly every 20 days, new liquidity pools are formed on both sides of the market, and the IPDA begins targeting them.

#### Step-by-Step IPDA Trade Flow

This is the exact sequence I run when trading inside the IPDA framework. Save it, print it, do not skip a step.

  1. **Identify the current quarterly shift** on the weekly or daily chart. Has the market changed direction in the last 3 to 4 months? Where is price within that cycle — early, middle, late?
  2. **Mark the 20-, 40-, and 60-day highs and lows** on the daily chart. These are the IPDA’s institutional reference levels.
  3. **Identify the next major draw on liquidity** — the closest of the three reference levels in the direction of the daily bias.
  4. **Wait for the false breakout** beyond the 20-day high or low. The IPDA typically takes liquidity at the 20-day extreme before reversing toward the 40- or 60-day level on the opposite side.
  5. **Drop to the intraday chart** at the 20-day extreme tap. Watch for the [ICT Kill Zone](<https://innercircletrader.net/tutorials/master-ict-kill-zones/>) windows — London open, NY AM, NY PM — for clean reversal timing.
  6. **Confirm the reversal** with an [ICT Market Structure Shift](<https://innercircletrader.net/tutorials/ict-market-structure-shift/>) on the lower timeframe in the direction of the daily bias.
  7. **Mark the PD Array** created during the displacement leg of the reversal — fair value gap, breaker block, or order block.
  8. **Position via[Optimal Trade Entry](<https://innercircletrader.net/tutorials/ict-optimal-trade-entry-ote-pattern/>)** on the retest of the displacement leg’s PD Array.
  9. **Take profit at the next IPDA reference level** in the trade direction — the 40-day or 60-day extreme.

![ICT IPDA trading example — 20-day liquidity raid, kill-zone reversal, MSS, OTE entry, target at 40-day level](https://innercircletrader.net/wp-content/uploads/2024/03/ICT-IPDA-Trading.png)

#### How to Trade ICT IPDA Data Ranges

When price creates a new 20-day high or low, the next step is waiting for liquidity to be taken at that level. This typically appears as a false breakout beyond the previous 20-day extreme — the IPDA’s classic stop-hunt before reversal.

To execute the trade, switch to the intraday chart and observe the key time windows known as ICT Kill Zones. Look for signs of reversal — particularly an ICT Market Structure Shift — and position yourself via Optimal Trade Entry on the retracement.

The pattern repeats: liquidity raid at the 20-day → kill-zone reversal → MSS confirmation → OTE entry → target the 40-day or 60-day extreme on the opposite side.

#### USA Trading Note — ES & NQ Futures

For US-based traders, IPDA cycles run cleanest on US index futures — **NASDAQ 100 (NQ Futures)** and the **E-mini S &P 500 (ES Futures)**. The CME futures session structure makes the 20/40/60-day cycles very clear because there is no weekend gap noise to muddy the read. ES and NQ are CFTC-regulated futures and execute through a US futures broker (NinjaTrader, AMP, Tradovate, or a prop firm such as Topstep). The major USD forex pairs (GBP/USD, EUR/USD) and Gold (XAU/USD) also respect IPDA delivery cleanly. TradingView is for chart analysis only.

#### Common Mistakes I See Traders Make on IPDA

Five mistakes account for the majority of failed IPDA trades I see in the comments. Avoid these and the framework converts at a much higher rate.

  1. **Treating IPDA as a random unpredictable force.** The whole point of IPDA is that price delivery is rule-based. If you are throwing up your hands and calling moves “random,” you have not yet read the IPDA correctly. Mark the levels and the rotation becomes visible.
  2. **Skipping the 20/40/60-day level marking.** The IPDA’s institutional reference levels are the foundation. Without them, you are guessing where the next move targets. Mark the three levels at the start of every week.
  3. **Trading IPDA without a daily bias.** The IPDA always has direction. Without your own daily bias, you cannot tell whether the next move is a liquidity raid (against the bias) or the real move (with the bias).
  4. **Entering before the kill-zone window.** IPDA reversals typically print inside the London open, NY AM, or NY PM kill zones. Setups that print at 11:30 AM or during Asia lunch are weaker — wait for the kill-zone timing.
  5. **Targeting beyond the next IPDA reference.** The algorithm pays at the next 20/40/60-day extreme in the trade direction. Setting take profit beyond that level is greed — the algorithm rotates rather than running indefinitely.

#### Final Thoughts

To trade IPDA effectively, master daily and weekly bias first. As ICT teaches, the market moves from liquidity to imbalance and from imbalance to liquidity. The strategy is simple: wait for external range liquidity to be taken, then watch for displacement in the opposite direction. Markets move from consolidation to expansion, not from consolidation directly to reversal. If price expands higher or lower, wait for a retracement and enter via the relevant [ICT PD Array](<https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/>).

#### FAQs About ICT IPDA

**What does IPDA stand for?**

IPDA stands for Interbank Price Delivery Algorithm — the algorithmic system Michael Huddleston taught to explain how institutions deliver price in forex and futures markets. It governs the 20-, 40-, and 60-day cycles and the quarterly shifts that drive larger directional moves.

**Is the Price Delivery Algorithm a myth?**

No. IPDA is not a myth. There is a clear set of rules controlling price delivery — visible in the 20/40/60-day cycles, the quarterly shifts, and the consistent liquidity-raid patterns at established highs and lows. Once you mark the levels, the algorithm becomes obvious.

**What is the IPDA data range?**

The IPDA data range is the previous 20, 40, or 60 days of price history used to identify the next major draw on liquidity. Marking the highs and lows of these ranges gives the institutional reference points for weekly and daily bias and for executing trades.

**What is the IPDA market cycle?**

After approximately every 20 days, a shift in price delivery prints on the daily chart — known as the IPDA lookback period. According to Michael Huddleston, new liquidity pools are created on both sides of the market roughly every 20 days, and the IPDA begins targeting them.

**What is the IPDA quarterly shift?**

The IPDA quarterly shift is the directional change that occurs every 3 to 4 months on most major instruments. The market resets and alters direction at this cycle, with institutions deliberately driving the change to harvest liquidity at both ends of the prior trend.

**Does the IPDA target retail traders specifically?**

The IPDA does not know about individual retail traders, but it does target the levels where retail stops cluster — old highs and old lows. Retail traders lose disproportionately because they place their stops at exactly the levels the IPDA is programmed to raid.

**Can the IPDA be conquered?**

Not entirely. But with a clear understanding of the 20/40/60-day cycles, the quarterly shifts, the IRL/ERL rotation, and the kill-zone timing, the win rate on aligned trades climbs significantly.

**What instruments respect IPDA delivery best?**

US index futures (NASDAQ 100 / NQ and E-mini S&P 500 / ES) show IPDA cycles cleanest because the CME session structure produces unbroken 20/40/60-day data. The major USD forex pairs (GBP/USD, EUR/USD) and Gold (XAU/USD) also respect IPDA delivery reliably.

**What is the relationship between IPDA and the kill zones?**

The IPDA cycles tell me when (which day) and where (which level) to expect a move. The kill zones tell me what time of day inside that move to actually execute. The two work together — IPDA for the directional anchor, kill zones for the entry timing.

#### ICT Inter Bank Price Delivery Algorithm – IPDA PDF Download

You can download below ICT inter bank price delivery algorithm – ipda in PDF for free. This PDF is sponsored by [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

[Download PDF](<https://ICTPULL.b-cdn.net/ICT%20PDF%203/ICT%20Inter%20Bank%20Price%20Delivery%20Algorithm%20-%20IPDA%20PDF%20Download.pdf>)

To learn complete ICT Trading strategy step by step, you can buy [ICT Trading PDF eBook](<http://www.ictpdf.com> "ICT Trading PDF") on [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")
