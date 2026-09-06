---
title: "ICT Macro Times — Complete Guide to the 09:50 NY-AM Macro & Other Windows + Free PDF"
source: "https://innercircletrader.net/tutorials/ict-macro-time-based-strategy/"
type: "tutorial"
date: "2024-10-26T09:23:02"
modified: "2026-05-07T21:53:26"
categories:
  - "ICT Trading Tutorials"
tags:
  - "ICT macro"
  - "ICT macro strategy"
  - "ICT macro time"
  - "ICT macro trading"
excerpt: "ICT Macro Times are short, scheduled windows during which the algorithm seeks liquidity or reprices a fair value gap. The foundation of these macros lies in ICT time and price theory. A macro is “A short order of instructions that creates an event in price delivery” as said by the ICT himself. ICT macros are …"
scraped_at: "2026-07-27T15:51:35.042696+00:00"
---

# ICT Macro Times — Complete Guide to the 09:50 NY-AM Macro & Other Windows + Free PDF

**Source:** [https://innercircletrader.net/tutorials/ict-macro-time-based-strategy/](https://innercircletrader.net/tutorials/ict-macro-time-based-strategy/)

Select Timezone

Session | Opening Time | Closing Time  
---|---|---  
London Macro |  |   
London Macro 2 |  |   
NY AM Macro |  |   
NY Macro AM 2 |  |   
NY AM Macro 3 |  |   
NY Lunch Macro |  |   
NY PM Macro |  |   
NY Last Hour Macro |  |   
  
![ICT Macro Times — short windows during which the algorithm seeks liquidity or rebalances fair value gaps in the London, NY-AM, NY lunch and NY-PM sessions](https://innercircletrader.net/wp-content/uploads/2024/05/ICT-Macro-Time-Based-Strategy.png)

ICT Macro Times are short, scheduled windows during which the algorithm seeks liquidity or reprices a fair value gap. The foundation of these macros lies in ICT time and price theory.

**A macro is “A short order of instructions that creates an event in price delivery”** as said by the **ICT himself.**

ICT macros are not complete trading strategies on their own, but they add powerful confluence and can sharpen the timing of an entry. They occur in the London session, the New York AM session, the New York lunch hour and the New York PM session.

In this guide I have compiled everything I rely on personally — the EST and GMT schedule, the 09:50 NY-AM example, the best pairs, the indicator, the daylight-saving rule, and the common mistakes traders make when they first start trading the windows.

You can jump to the section you are most interested in from below or continue reading the full article for a complete understanding.

Table of Contents

[Toggle](<#>)

#### What are ICT Macro Times?

A macro is **“A short order of instructions that creates an event in price delivery”** as said by the ICT himself.

ICT Macro Times are short intervals during which the algorithm seeks liquidity (sell-side or buy-side) or reprices a fair value gap. As mentioned earlier, they are based on ICT time and price theory and they sit on top of the broader [ICT PD Array](<https://innercircletrader.net/tutorials/ict-pd-array-key-to-trade-execution/>) framework.

You can use ICT macros to enhance an existing setup because the windows add confluence to the entry rather than replacing the trade idea.

In his 2024 Mentorship ICT mentioned that **“ICT macro happens in every single hour containing last 10 minutes of closing hour and first 10 minutes of opening hour”** with a few exceptions noted later in this article.

Michael Huddleston also mentioned in his 2024 Mentorship that **“Last hour has four macros”** which means an ICT Macro occurs after every 15 minutes during the last hour of the regular session.

ICT macros were initially introduced by Michael Huddleston in 2023 and this is how they look on the chart.

![ICT Macros plotted on a 5-minute index chart — repeating short windows in London, NY-AM, NY lunch and NY-PM](https://innercircletrader.net/wp-content/uploads/2024/05/ICT-Macro-1.png)

#### How ICT Macros Work

During the ICT macro time the algorithm either seeks liquidity (sell-side or buy-side) or it works to balance the imbalance — the fair value gap — in price.

A trading setup may form before the macro window, and the macro itself adds the volatility that delivers the move into liquidity. Sometimes the setup forms inside the window and reaches its target inside the same window.

So before the opening of any ICT macro, I mark the imbalance and draw on liquidity above and below current price.

You do not need a fixed bias for the day to trade a macro — only a clean directional read for that specific window. I find that read with two simple rules:

(I) If price has taken sell-side liquidity, I expect price to move up to take buy-side liquidity or balance any imbalance left above.

(II) If price has taken buy-side liquidity, I expect price to move down to take sell-side liquidity or balance any imbalance left below.

After I have a clear direction I wait for an ICT macro to open and then initiate the trade.

You can also use ICT macros in conjunction with other ICT trading strategies — the [ICT 2022 Trading Model](<https://innercircletrader.net/tutorials/complete-ict-trading-strategy-2022/>), the [ICT Silver Bullet](<https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/>) or a [Judas Swing](<https://innercircletrader.net/tutorials/ict-judas-swing-complete-guide/>) — to maximise the quality of the entry.

A real ICT macro time example is given below.

![US30 15-minute chart before the 09:50 AM ICT macro — buy-side liquidity has already been taken so the next draw is sell-side](https://innercircletrader.net/wp-content/uploads/2024/05/ICT-Macro-2.png)

In the picture above you can see the US30 15-minute chart before the 09:50 AM macro and price has already taken the buy-side liquidity.

![US30 5-minute chart after the 09:50 AM ICT macro — market structure shifts to the sell side and price retraces into the FVG mean threshold for the entry](https://innercircletrader.net/wp-content/uploads/2024/05/ICT-Macro-3.png)

This is the US30 5-minute chart and you can see that after the 09:50 AM ICT macro, price shifted its structure to the sell side.

  * The buy-side has been taken and price is looking for sell-side liquidity.
  * After the [ICT Market Structure Shift](<https://innercircletrader.net/tutorials/ict-market-structure-shift/>), price traded back to the [ICT Fair Value Gap](<https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/>).
  * A sell trade was executed at the [Mean Threshold](<https://innercircletrader.net/tutorials/ict-consequent-encroachment/>) of the fair value gap with stop loss above the FVG candle’s high.
  * For take profit I targeted the relative equal lows and price almost grabbed the low, delivering 40 handles at a 1:3 risk-reward ratio.

#### ICT Macro Times EST & GMT (Schedule)

Below I have tabulated the macro windows in both EST and GMT so there is no confusion about your local zone.

ICT Macros| EST Time| GMT Time  
---|---|---  
London Macro| 02:33 AM to 03:00 AM| 06:33 AM – 07:00 AM  
London Macro| 04:03 AM to 04:30 AM| 08:03 AM – 08:30 AM  
New-York AM Macro| 08:50 AM to 09:10 AM| 12:50 PM – 01:10 PM  
New-York AM Macro| 009:50 AM to 10:10 AM| 01:50 PM – 02:10 PM  
New-York AM Macro| 10:50 AM to 11:10 AM| 02:50 PM – 03:10 PM  
New York Lunch Macro| 11:50 AM to 12:10 PM| 03:50 PM – 04:10 PM  
New York PM Macro| 01:10 PM to 01:40 PM| 05:10 PM – 05:40 PM  
New York Last Hour Macro| 03:15 PM to 03:45 PM| 07:15 PM – 07:45 PM  
  
The cleanest way to remember the schedule is to anchor to New York local time and let your charting software adjust GMT for you. New York is the reference clock that ICT himself recommends.

#### Step-by-Step Macro Trade Flow

This is the exact sequence I run before every macro window — from pre-market prep to trade management.

  1. **Mark the draw on liquidity** — relative equal highs/lows, prior day high/low, prior session high/low and any week-opening gap that is still unfilled.
  2. **Mark the imbalances** — every unfilled fair value gap above and below current price on the 15-minute and 5-minute timeframes.
  3. **Read direction** — if buy-side has just been swept, the next draw is sell-side, and vice versa. This becomes the bias for the window.
  4. **Wait for the window to open** — do not pre-position; the macro itself is the catalyst, so the entry must come after the window starts.
  5. **Look for displacement and an MSS** — a clean break of the most recent short-term high or low confirms intent.
  6. **Enter on the retracement** — into the fair value gap, the order block or the mean threshold left behind by displacement.
  7. **Stop loss** — above the high of the displacement candle for shorts, below the low for longs.
  8. **Take profit** — at the next pool of liquidity (relative equal lows/highs, session low/high or unfilled FVG).
  9. **Manage at first liquidity** — move stop to break-even once price reaches the first internal liquidity pool, then trail.

#### Types of Liquidity for ICT Macros

These are the seven liquidity reads I scan for before any macro opens — they are also covered in detail in my [internal vs external liquidity](<https://innercircletrader.net/tutorials/ict-internal-external-liquidity/>) guide.

(I) Previous day high/low draw on liquidity.

(II) Previous session high/low draw on liquidity.

(III) Established high/low on the 15-minute chart.

(IV) Previous week high/low draw on liquidity.

(V) Return to the current or old week opening gap.

(VI) Expansion away from the current or old week opening gap.

(VII) Relative equal highs or lows.

#### Best Time Frame for ICT Macros

ICT macros involve a short interval of time, so the lower timeframes are ideal for execution.

I use the 15-minute timeframe to find direction and to spot the liquidity or imbalance in price, and then I drop down to the 5-minute, 3-minute or 1-minute chart to time the entry once the window opens.

The 1-minute chart is especially useful inside the 09:50–10:10 AM window because the move tends to deliver in tight, fast bursts and a lower timeframe MSS is the cleanest trigger.

#### Best Pairs for ICT Macros

The ICT Macro strategy was initially developed and tested on indices such as NASDAQ (NQ Futures) and E-mini S&P 500 (ES), which proved to be the most effective trading instruments for this approach.

Over time, traders began applying the ICT Macro strategy to forex and metals markets with strong results.

Today the ICT Macro strategy has demonstrated its efficacy across major forex pairs like GBP/USD and EUR/USD as well as on precious metals like XAU/USD, showcasing its versatility and reliability across diverse trading environments.

**For traders in the United States** who follow the CFTC FIFO and no-hedge rules, NQ and ES futures (CME Group) are the most natural fit for macro trading because they are deep, regulated indices with no short-restriction issues. Many of my US-based readers also use micro-lot futures (MNQ, MES) to keep risk per macro window proportionate to a smaller account.

#### Best ICT Macro Time to Trade

The New York AM macro is the strongest window in my own log because of New York session volatility and the overlap with the late London session. Most of the day’s high-impact news releases also land inside this window.

If you are trading stock futures or indices, the 09:50 to 10:10 NY-AM macro is ideal because the New York Stock Exchange opens at 09:30 and order flow is at its peak by 09:50.

#### ICT Macros Indicator (TradingView)

You can add the ICT Macros [LuxAlgo] indicator on your charts in TradingView.

Open the indicators tab in TradingView and search “ICT Macros”. The ICT Macros [LuxAlgo] indicator will appear in the first or second result.

To apply the indicator, click on it and it will activate on the chart.

It is important to mention here that it only works on 5-minute or lower timeframes.

You can also open the indicator’s settings to personalise it according to your preference — different colours per session, on/off toggles for individual windows, and label positioning.

#### How does Daylight Saving Time Affect ICT Macro Times?

Daylight Saving Time (DST) in the US is a practice where clocks are moved forward one hour in the spring, giving more daylight hours in the evening during the summer months, and then moved back one hour in the fall to return to standard time.

Essentially “springing forward” in March and “falling back” in November, with the time change occurring on the second Sunday of March and the first Sunday of November respectively, at 2:00 AM local time.

If your country does not follow daylight saving time then it can affect the ICT Macro times relative to your local time with a shift of an hour.

But if your country follows daylight saving time then you do not need to worry about it.

To avoid any confusion, ICT himself recommends following New York local time as the base time. It does not matter where you live — just follow the NY local clock.

The session and macro windows remain the same irrespective of daylight saving; only the label of the time itself changes from EST (Eastern Standard Time) to EDT (Eastern Daylight Saving Time).

#### Common Mistakes When Trading ICT Macros

These are the recurring mistakes I see among traders who first start trading the macro windows.

  1. **Pre-positioning before the window opens.** The macro itself is the catalyst. Entering before the window opens removes the entire reason for using the strategy.
  2. **Trading every macro of the day.** Not every window has a clean draw on liquidity. If there is no obvious target above or below, sit out and wait for the next one.
  3. **Ignoring news releases.** A high-impact release inside the window distorts price action. I avoid the macro window if a red-folder news event prints inside it.
  4. **Using the LuxAlgo indicator on a higher timeframe.** The indicator only renders correctly on 5-minute or lower charts. On 15-minute and above it will not display the windows.
  5. **Forgetting daylight saving.** Twice a year the EST/EDT label changes. If you trade from a fixed local clock, your entry will be off by an hour for two weeks until your charting platform syncs.
  6. **No stop loss or moving the stop further away.** Macro windows are short and the volatility resolves quickly. A predefined stop above the displacement candle’s high (or below the low) is non-negotiable.

#### ICT Macro Times PDF Download

You can download below ICT macro times in PDF for free. This PDF is sponsored by [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

[Download PDF](<https://ICTPULL.b-cdn.net/ICT%20PDF%202/ICT%20Macro%20Times%20PDF%20Download.pdf>)

To learn the complete ICT Trading strategy step by step, you can buy the [ICT Trading PDF eBook](<http://www.ictpdf.com> "ICT Trading PDF") on [**ICTPDF.COM.**](<http://www.ictpdf.com> "ICT Trading PDF")

#### FAQs about ICT Macro Times

Here are brief answers to the questions readers ask most often about ICT Macro Times.

**What are ICT Macro Times?**

ICT Macro Times are specific intervals during which the algorithm seeks liquidity or reprices a fair value gap, based on ICT’s time and price theory.

**How do ICT Macros work?**

ICT Macros create events in price delivery by seeking liquidity or balancing price imbalances during designated time windows.

**Why should I incorporate ICT Macros into my trading strategy?**

Incorporating ICT Macros enhances your trading strategy by adding confluence and improving the potential for profitable trades.

**When do ICT Macros occur?**

ICT Macros typically occur during the London session, the New York AM session, the New York lunch hour and the New York PM session.

**What is a macro in trading terms?**

A macro is described by ICT as a “short order of instructions that creates an event in price delivery”.

**What types of liquidity should I look for during ICT Macros?**

Look for previous day highs/lows, established highs/lows on charts and relative equal highs/lows as liquidity draws.

**What time frame is best for trading ICT Macros?**

Lower time frames, particularly 1-minute to 15-minute charts, are ideal for spotting liquidity and executing trades during ICT Macros.

**Which trading pairs work best with ICT Macros?**

The ICT Macro strategy is effective with major forex pairs like GBP/USD and EUR/USD, with index futures like NQ and ES, and with precious metals like XAU/USD.

**What are the best times to trade ICT Macros?**

New York AM macros are generally considered the best time due to high volatility and overlapping trading sessions.

**Can I trade stocks using ICT Macros?**

Yes, ICT Macros can be applied to stock futures and indices, particularly during the New York AM session at the 09:50–10:10 window.

**How can I identify ICT Macro times on my trading chart?**

You can use the ICT Macros [LuxAlgo] indicator on TradingView to identify these times and visualise macro events.

**What is the role of liquidity in ICT Macros?**

Liquidity is essential during ICT Macros as it indicates where price may move, allowing traders to capitalise on potential market shifts.

**How many ICT Macros occur in the last hour of trading?**

According to ICT, there are four macros in the last hour, with an event happening every 15 minutes.

**Can ICT Macros be used with other trading strategies?**

Yes, ICT Macros can be effectively combined with other ICT trading strategies, such as the ICT 2022 Model or the ICT Silver Bullet.

**Is there a specific indicator for ICT Macros?**

Yes, the ICT Macros [LuxAlgo] indicator can be found on TradingView and is suitable for use on 5-minute or lower time frames.

**Are there any exceptions to ICT Macro timings?**

Yes, while ICT Macros generally occur within specified time frames, there may be exceptions as mentioned in ICT’s mentorship materials.

**What is the importance of the last 10 minutes of trading?**

The last 10 minutes of closing and the first 10 minutes of opening hours are critical, as they often experience heightened volatility and liquidity changes.

**What can impact the effectiveness of ICT Macros?**

Market conditions, economic news releases and trader sentiment can impact the effectiveness of ICT Macros.

**Can beginners effectively trade using ICT Macros?**

Yes, beginners can benefit from understanding and using ICT Macros, especially when combined with other foundational trading strategies and a clear [daily bias](<https://innercircletrader.net/tutorials/ict-daily-bias-explained/>).
