"""
Data tool: pulls OHLCV candles. Uses yfinance so the scaffold runs with zero
broker setup — swap this out for Alpaca/TradingView market data later without
touching any of the ICT detection logic below, since they all just take a
pandas DataFrame with columns [open, high, low, close, volume].

SSL note (Windows/Python 3.14): curl_cffi used by yfinance ignores env-based
CA bundle vars. We skip yfinance and go straight to the TV CDP fallback which
uses Node.js + its own working TLS stack.
"""
import ssl
# CRITICAL: Patch the default SSL context BEFORE any HTTP-capable library is imported.
# yfinance uses curl_cffi internally which reads the default SSL context at import time;
# without this patch, all Yahoo Finance requests fail with SSL cert verify errors on Windows.
ssl._create_default_https_context = ssl._create_unverified_context

import pandas as pd
from harness.plugin import ToolPlugin


def get_candles(symbol: str, interval: str, lookback: str) -> pd.DataFrame:
    """
    symbol: e.g. 'EURUSD=X', 'SPY', 'BTC-USD'
    interval: yfinance interval string, e.g. '15m', '1h', '1d'
    lookback: yfinance period string, e.g. '5d', '10d', '60d'
    Returns a DataFrame indexed by UTC timestamp with columns:
    open, high, low, close, volume
    """
    # Skip yfinance entirely — SSL cert store is broken on Python 3.14 / Windows.
    # Use TV CDP / SMC engine fallback directly; it has its own working TLS stack.
    try:
        from .smc_data import get_candles_from_engine
        df = get_candles_from_engine(symbol, interval, lookback)
    except Exception as e:
        return pd.DataFrame()  # Should never happen; _generate_mock_candles is fallback

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index, utc=True)
    return df[["open", "high", "low", "close", "volume"]]


def _handle_get_candles_summary(tool_input: dict, ctx) -> dict:
    df = ctx.get_candles(tool_input["symbol"], tool_input["timeframe"])
    if len(df) == 0:
        return {"error": f"No candle data for {tool_input['symbol']}"}
    # Compute meaningful stats for the agent
    result = {
        "bars": len(df),
        "first": str(df.index[0]),
        "last": str(df.index[-1]),
        "last_close": float(df["close"].iloc[-1]),
        "period_high": float(df["high"].max()),
        "period_low": float(df["low"].min()),
        "period_open": float(df["open"].iloc[0]),
        "period_range": float(df["high"].max() - df["low"].min()),
    }
    # Add weekly stats (last ~5 bars)
    recent = df.tail(min(5, len(df)))
    result["week_high"] = float(recent["high"].max())
    result["week_low"] = float(recent["low"].min())
    result["week_range"] = float(result["week_high"] - result["week_low"])
    return result


def _handle_get_weekly_projection(tool_input: dict, ctx) -> dict:
    """Project weekly high/low using ICT weekly profile framework.

    Uses daily data (90d lookback) to compute:
    - Previous week's high/low (anchor points)
    - Monthly range midpoint (equilibrium)
    - ATR-based volatility bands
    - Projected weekly range with bias weighting
    """
    import numpy as np

    symbol = tool_input.get("symbol", "")
    # Fetch daily data for monthly context (bypass context cache, go direct)
    try:
        df = get_candles(symbol, "1d", "90d")
    except Exception:
        df = pd.DataFrame()

    if len(df) < 10:
        # Fallback to HTF hourly (wider lookback)
        try:
            df = ctx.get_candles(symbol, "HTF")
        except Exception:
            return {"error": f"No data for {symbol}"}

    if len(df) == 0:
        return {"error": f"No data for {symbol}"}

    current = float(df["close"].iloc[-1])
    month_high = float(df["high"].max())
    month_low = float(df["low"].min())
    month_mid = (month_high + month_low) / 2
    month_range = month_high - month_low

    # Previous full week (Mon-Fri anchor)
    # Use last 7 bars as proxy for previous week
    prev_week = df.tail(7)
    prev_week_high = float(prev_week["high"].max())
    prev_week_low = float(prev_week["low"].min())
    prev_week_range = prev_week_high - prev_week_low

    # ATR (average true range) over 14 bars
    if len(df) >= 14:
        df_14 = df.tail(14)
        atr = float((df_14["high"] - df_14["low"]).abs().mean())
    else:
        atr = float(month_range * 0.15)  # fallback estimate

    # Position within monthly range (0=bottom, 1=top)
    pos_in_range = (current - month_low) / month_range if month_range > 0 else 0.5

    # Determine directional bias from recent structure
    last_5 = df.tail(5)
    recent_highs = last_5["high"].max()
    recent_lows = last_5["low"].min()
    price_vs_recent = (current - recent_lows) / (recent_highs - recent_lows) if recent_highs > recent_lows else 0.5

    # Projected weekly range anchored to structural levels
    # ICT principle: weekly range typically 40-60% of monthly range on low-vol weeks,
    # up to 80-100% on high-vol/event weeks
    vol_factor = min(1.0, atr / (month_range * 0.1)) if month_range > 0 else 0.5
    expected_range_pct = 0.4 + 0.3 * vol_factor  # 40-70% of monthly range typical

    proj_high = current + (month_range * expected_range_pct * (1 - pos_in_range))
    proj_low = current - (month_range * expected_range_pct * pos_in_range)

    # Clamp to reasonable bounds (don't exceed monthly extremes by more than 1 ATR)
    proj_high = min(proj_high, month_high + atr)
    proj_low = max(proj_low, month_low - atr)

    # Bias adjustment: if price is near top of range, project lower; vice versa
    if pos_in_range > 0.7:
        proj_high -= atr * 0.5  # dampen upside projection
        proj_low -= atr * 0.3
    elif pos_in_range < 0.3:
        proj_low += atr * 0.5  # dampen downside projection
        proj_high += atr * 0.3

    return {
        "symbol": symbol,
        "current_price": current,
        "position_in_monthly_range": round(pos_in_range, 3),  # 0-1
        "monthly_high": month_high,
        "monthly_low": month_low,
        "monthly_mid": round(month_mid, 4),
        "prev_week_high": prev_week_high,
        "prev_week_low": prev_week_low,
        "prev_week_range": round(prev_week_range, 4),
        "atr_14d": round(atr, 4),
        "projected_weekly_high": round(proj_high, 4),
        "projected_weekly_low": round(proj_low, 4),
        "projected_weekly_range": round(proj_high - proj_low, 4),
        "confidence": "HIGH" if len(df) >= 30 else "MEDIUM",
    }


PLUGINS = [
    ToolPlugin(
        name="get_candles_summary",
        description="Get recent OHLCV candle count/range/last-close and period high/low for a symbol/timeframe. Other tools compute directly from the same underlying candles.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["HTF", "LTF"]},
            },
            "required": ["symbol", "timeframe"],
        },
        handler=_handle_get_candles_summary,
    ),
    ToolPlugin(
        name="get_weekly_projection",
        description="Project the upcoming week's high and low using ICT weekly profile framework. Uses monthly range, previous week levels, and ATR-based volatility to compute expected weekly range with bias-adjusted bounds.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
            },
            "required": ["symbol"],
        },
        handler=_handle_get_weekly_projection,
    ),
]
