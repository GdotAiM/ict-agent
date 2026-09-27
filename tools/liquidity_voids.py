"""
Liquidity Voids: gaps between swing points larger than 2x ATR.

In ICT doctrine, a liquidity void (or "liquidity gap") is a zone where price
moved so aggressively that very few orders were traded in that region.
Price often returns to fill these voids before continuing — they act as
strong magnets similar to FVGs but at a higher timeframe.

Detection: a void exists between two consecutive swing highs (or lows) when
the distance exceeds 2x the recent ATR. The void spans from the lower swing
to the higher swing, with no meaningful price action in between.
"""
import pandas as pd
from .structure import get_market_structure
from harness.plugin import ToolPlugin


def get_liquidity_voids(df: pd.DataFrame, atr_mult: float = 2.0,
                        min_bars_between: int = 3,
                        max_results: int = 5) -> list:
    """
    Detect liquidity voids in the given DataFrame.

    Args:
        df: OHLCV DataFrame with columns [open, high, low, close]
        atr_mult: Multiples of ATR to consider as a void threshold
        min_bars_between: Minimum bars between swing points to qualify
        max_results: Maximum number of voids to return

    Returns:
        List of dict with keys: type, top, bottom, atr, size_pct, swept
    """
    if len(df) < 15:
        return []

    # Calculate ATR
    tr = (df["high"] - df["low"]).rolling(14).mean()
    fallback_atr = float(tr.mean()) if not pd.isna(tr).all() else float(df["high"].max() - df["low"].min()) * 0.5
    atr_values = [float(v) if not pd.isna(v) else fallback_atr for v in tr.values]

    # Get market structure swings
    structure = get_market_structure(df)
    swing_highs = structure.get("swing_highs", [])
    swing_lows = structure.get("swing_lows", [])

    voids = []

    # Check for voids between swing highs (bearish void - price skipped up)
    for i in range(len(swing_highs) - 1):
        t1, h1 = swing_highs[i]
        t2, h2 = swing_highs[i + 1]

        # Need sufficient time separation
        if hasattr(t1, 'timestamp') and hasattr(t2, 'timestamp'):
            bars_between = abs((t2 - t1).total_seconds() / 3600)  # rough hour estimate
        else:
            bars_between = i + 1  # fallback estimate

        if bars_between < min_bars_between:
            continue

        # Void if high moved significantly without proportional body
        void_size = abs(h2 - h1)
        atr_idx = min(i + 7, len(atr_values) - 1)  # approximate ATR at this point
        current_atr = atr_values[atr_idx] if atr_idx < len(atr_values) else fallback_atr

        if void_size > current_atr * atr_mult:
            # Determine if void was swept (price entered it)
            last_close = float(df["close"].iloc[-1])
            low_price = min(h1, h2)
            high_price = max(h1, h2)
            swept = low_price <= last_close <= high_price

            voids.append({
                "type": "bearish_void",
                "top": float(high_price),
                "bottom": float(low_price),
                "atr": round(current_atr, 4),
                "size_pct": round(void_size / current_atr * 100, 1),
                "swept": swept,
                "formed_at": str(t2),
            })

    # Check for voids between swing lows (bullish void - price skipped down)
    for i in range(len(swing_lows) - 1):
        t1, l1 = swing_lows[i]
        t2, l2 = swing_lows[i + 1]

        if hasattr(t1, 'timestamp') and hasattr(t2, 'timestamp'):
            bars_between = abs((t2 - t1).total_seconds() / 3600)
        else:
            bars_between = i + 1

        if bars_between < min_bars_between:
            continue

        void_size = abs(l2 - l1)
        atr_idx = min(i + 7, len(atr_values) - 1)
        current_atr = atr_values[atr_idx] if atr_idx < len(atr_values) else fallback_atr

        if void_size > current_atr * atr_mult:
            last_close = float(df["close"].iloc[-1])
            low_price = min(l1, l2)
            high_price = max(l1, l2)
            swept = low_price <= last_close <= high_price

            voids.append({
                "type": "bullish_void",
                "top": float(high_price),
                "bottom": float(low_price),
                "atr": round(current_atr, 4),
                "size_pct": round(void_size / current_atr * 100, 1),
                "swept": swept,
                "formed_at": str(t2),
            })

    # Sort by size (largest first) and return top results
    voids.sort(key=lambda x: x["size_pct"], reverse=True)
    return voids[:max_results]


def _handle_get_liquidity_voids(tool_input: dict, ctx) -> dict:
    df = ctx.get_candles(tool_input.get('symbol', getattr(ctx, 'symbol', '')),
                         tool_input.get("timeframe", "HTF"))
    result = get_liquidity_voids(df)
    return {"voids": result, "count": len(result)}


PLUGINS = [
    ToolPlugin(
        name="get_liquidity_voids",
        description="Detects liquidity voids (large gaps between swing points >2x ATR). Voids act as price magnets — price often returns to fill them.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["HTF", "LTF"]},
            },
            "required": ["symbol", "timeframe"],
        },
        handler=_handle_get_liquidity_voids,
    ),
]
