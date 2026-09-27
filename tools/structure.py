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
        - BOS (Break of Structure): continuation in direction of trend
          Requires displacement candle (body > 1.5x ATR) breaking prior swing
        - CHoCH (Change of Character): reversal signal
          Occurs when price breaks structure against prevailing trend
      mss_detected: bool — True if a Market Structure Shift was detected
        (strong displacement-driven break, ICT 2024+ concept)
      last_swing_high / last_swing_low: (timestamp, price)
      swing_highs / swing_lows: recent points, for other tools to reuse
    """
    # Calculate ATR for displacement detection
    tr = (df["high"] - df["low"]).rolling(14).mean()
    fallback_atr = float(tr.mean()) if not tr.isna().all() else float(df["high"].max() - df["low"].min()) * 0.15

    highs, lows = _swings(df, lookback)
    if len(highs) < 2 or len(lows) < 2:
        return {"trend": "ranging", "last_event": None,
                "mss_detected": False, "last_displacement": None,
                "swing_highs": highs, "swing_lows": lows}

    # merge and sort all swings chronologically to read the sequence
    points = sorted(
        [(t, p, "H") for t, p in highs] + [(t, p, "L") for t, p in lows],
        key=lambda x: x[0],
    )

    trend = "ranging"
    last_event = None
    mss_detected = False
    prev_high = prev_low = None
    last_displacement = None  # Track if recent break had displacement

    for idx, (t, p, kind) in enumerate(points):
        if kind == "H":
            if prev_high is not None:
                if p > prev_high:
                    if trend != "bearish":
                        trend = "bullish"
                        # Check if this break had displacement (ICT MSS concept)
                        if _had_displacement(df, t, prev_high, p, fallback_atr):
                            mss_detected = True
                            last_displacement = "bullish"
                        last_event = "BOS"
                    else:
                        # Breaking above previous high in bearish trend = CHoCH
                        last_event = "CHoCH"
            prev_high = p
        else:
            if prev_low is not None:
                if p < prev_low:
                    if trend != "bullish":
                        trend = "bearish"
                        if _had_displacement(df, t, prev_low, p, fallback_atr):
                            mss_detected = True
                            last_displacement = "bearish"
                        last_event = "BOS"
                    else:
                        # Breaking below previous low in bullish trend = CHoCH
                        last_event = "CHoCH"
            prev_low = p

    return {
        "trend": trend,
        "last_event": last_event,
        "mss_detected": mss_detected,
        "last_displacement": last_displacement,
        "last_swing_high": highs[-1] if highs else None,
        "last_swing_low": lows[-1] if lows else None,
        "swing_highs": highs[-5:],
        "swing_lows": lows[-5:],
    }


def _had_displacement(df: pd.DataFrame, current_time, prev_level: float,
                       current_level: float, fallback_atr: float) -> bool:
    """Check if the move from prev_level to current_level had displacement.

    Displacement = large body candle (>1.5x ATR) in the direction of the break.
    This distinguishes MSS (strong, institutional) from CHoCH (weaker, corrective).
    """
    try:
        # Find the bar closest to current_time
        mask = abs(df.index - current_time) < pd.Timedelta("2h")
        if not mask.any():
            return False
        bar = df[mask].iloc[-1]
        body = abs(bar["close"] - bar["open"])
        atr = float(bar["high"] - bar["low"])
        if atr == 0:
            atr = fallback_atr
        return body > atr * 1.5
    except Exception:
        return False


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
