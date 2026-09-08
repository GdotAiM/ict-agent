"""
Market structure: swing highs/lows, and trend via BOS (break of structure,
continuation) vs CHoCH (change of character, reversal) — the ICT-standard
way to read what phase the market is in before doing anything else.
"""
import pandas as pd
from harness.plugin import ToolPlugin


def _swings(df: pd.DataFrame, lookback: int = 3):
    """Fractal swing points: a bar is a swing high/low if it's the extreme
    within `lookback` bars on each side."""
    highs, lows = [], []
    h, l = df["high"].values, df["low"].values
    for i in range(lookback, len(df) - lookback):
        window_h = h[i - lookback:i + lookback + 1]
        window_l = l[i - lookback:i + lookback + 1]
        if h[i] == window_h.max():
            highs.append((df.index[i], h[i]))
        if l[i] == window_l.min():
            lows.append((df.index[i], l[i]))
    return highs, lows


def get_market_structure(df: pd.DataFrame, lookback: int = 3) -> dict:
    """
    Returns:
      trend: 'bullish' | 'bearish' | 'ranging'
      last_event: 'BOS' | 'CHoCH' | None
      last_swing_high / last_swing_low: (timestamp, price)
      swing_highs / swing_lows: recent points, for other tools to reuse
    """
    highs, lows = _swings(df, lookback)
    if len(highs) < 2 or len(lows) < 2:
        return {"trend": "ranging", "last_event": None,
                "swing_highs": highs, "swing_lows": lows}

    # merge and sort all swings chronologically to read the sequence
    points = sorted(
        [(t, p, "H") for t, p in highs] + [(t, p, "L") for t, p in lows],
        key=lambda x: x[0],
    )

    trend = "ranging"
    last_event = None
    prev_high = prev_low = None

    for t, p, kind in points:
        if kind == "H":
            if prev_high is not None:
                if p > prev_high and trend != "bearish":
                    trend, last_event = "bullish", "BOS"
                elif p > prev_high and trend == "bearish":
                    trend, last_event = "bullish", "CHoCH"
            prev_high = p
        else:
            if prev_low is not None:
                if p < prev_low and trend != "bullish":
                    trend, last_event = "bearish", "BOS"
                elif p < prev_low and trend == "bullish":
                    trend, last_event = "bearish", "CHoCH"
            prev_low = p

    return {
        "trend": trend,
        "last_event": last_event,
        "last_swing_high": highs[-1] if highs else None,
        "last_swing_low": lows[-1] if lows else None,
        "swing_highs": highs[-5:],
        "swing_lows": lows[-5:],
    }


def _handle_get_market_structure(tool_input: dict, ctx) -> dict:
    df = ctx.get_candles(tool_input.get('symbol', getattr(ctx, 'symbol', '')), tool_input["timeframe"])
    return get_market_structure(df)


PLUGINS = [
    ToolPlugin(
        name="get_market_structure",
        description="Returns trend (bullish/bearish/ranging) and last structural event (BOS or CHoCH) for a symbol/timeframe.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["HTF", "LTF"]},
            },
            "required": ["symbol", "timeframe"],
        },
        handler=_handle_get_market_structure,
    ),
]
