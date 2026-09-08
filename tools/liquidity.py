"""
Liquidity: where resting stop orders (retail liquidity) are likely pooled —
equal highs/lows and prior swing extremes — and whether price has recently
swept one (wicked through and closed back inside/opposite), which is the
classic ICT tell that a reversal or continuation entry may be forming.
"""
import pandas as pd
from .structure import _swings
from harness.plugin import ToolPlugin


def get_liquidity_pools(df: pd.DataFrame, lookback: int = 3,
                         equal_tol_pct: float = 0.05) -> dict:
    """
    Returns buy-side liquidity (BSL, resting above highs) and sell-side
    liquidity (SSL, resting below lows), including simple equal-highs/
    equal-lows clusters within equal_tol_pct of each other.
    """
    highs, lows = _swings(df, lookback)

    def cluster(points, tol_pct):
        clusters = []
        used = set()
        for i, (t1, p1) in enumerate(points):
            if i in used:
                continue
            group = [(t1, p1)]
            for j, (t2, p2) in enumerate(points):
                if j <= i or j in used:
                    continue
                if abs(p2 - p1) / p1 * 100 <= tol_pct:
                    group.append((t2, p2))
                    used.add(j)
            if len(group) >= 2:
                avg = sum(p for _, p in group) / len(group)
                clusters.append({"level": avg, "touches": len(group),
                                  "points": group})
        return clusters

    bsl_equal = cluster(highs, equal_tol_pct)
    ssl_equal = cluster(lows, equal_tol_pct)

    return {
        "bsl": {
            "raw_highs": highs[-5:],
            "equal_highs": bsl_equal,
        },
        "ssl": {
            "raw_lows": lows[-5:],
            "equal_lows": ssl_equal,
        },
    }


def detect_sweep(df: pd.DataFrame, level: float, direction: str,
                  within_bars: int = 5) -> dict:
    """
    direction: 'above' (checking a BSL sweep) or 'below' (checking an SSL sweep)
    Looks at the most recent `within_bars` candles for a wick beyond `level`
    that closes back on the other side — the sweep + reversal signature.
    """
    recent = df.tail(within_bars)
    for t, row in recent.iterrows():
        if direction == "above" and row["high"] > level and row["close"] < level:
            return {"swept": True, "time": str(t), "wick_high": row["high"]}
        if direction == "below" and row["low"] < level and row["close"] > level:
            return {"swept": True, "time": str(t), "wick_low": row["low"]}
    return {"swept": False}


def _handle_get_liquidity_pools(tool_input: dict, ctx) -> dict:
    df = ctx.get_candles(tool_input.get('symbol', getattr(ctx, 'symbol', '')), tool_input["timeframe"])
    return get_liquidity_pools(df)


PLUGINS = [
    ToolPlugin(
        name="get_liquidity_pools",
        description="Returns buy-side (BSL) and sell-side (SSL) liquidity pools, including equal-highs/equal-lows clusters, for a symbol/timeframe.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["HTF", "LTF"]},
            },
            "required": ["symbol", "timeframe"],
        },
        handler=_handle_get_liquidity_pools,
    ),
]
