"""
Fair Value Gaps (FVG): the 3-candle imbalance ICT uses as a magnet/entry —
price often returns to "fill" the gap before continuing.
"""
import pandas as pd
from harness.plugin import ToolPlugin


def get_fair_value_gaps(df: pd.DataFrame, max_results: int = 10) -> list:
    gaps = []
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    idx = df.index

    for i in range(2, len(df)):
        # bullish FVG: candle[i-2].high < candle[i].low
        if h[i - 2] < l[i]:
            gaps.append({
                "type": "bullish",
                "top": float(l[i]),
                "bottom": float(h[i - 2]),
                "formed_at": str(idx[i]),
            })
        # bearish FVG: candle[i-2].low > candle[i].high
        if l[i - 2] > h[i]:
            gaps.append({
                "type": "bearish",
                "top": float(l[i - 2]),
                "bottom": float(h[i]),
                "formed_at": str(idx[i]),
            })

    # mark fill status against price after formation
    last_close = float(c[-1])
    for g in gaps:
        mid = (g["top"] + g["bottom"]) / 2
        if g["type"] == "bullish":
            g["filled"] = last_close < g["bottom"]
        else:
            g["filled"] = last_close > g["top"]
        g["midpoint"] = mid

    unfilled = [g for g in gaps if not g["filled"]]
    return unfilled[-max_results:] if unfilled else gaps[-max_results:]


def _handle_get_fair_value_gaps(tool_input: dict, ctx) -> dict:
    df = ctx.get_candles(tool_input.get('symbol', getattr(ctx, 'symbol', '')), tool_input["timeframe"])
    return {"fvgs": get_fair_value_gaps(df)}


PLUGINS = [
    ToolPlugin(
        name="get_fair_value_gaps",
        description="Returns unfilled fair value gaps (bullish/bearish) on the given symbol/timeframe.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["HTF", "LTF"]},
            },
            "required": ["symbol", "timeframe"],
        },
        handler=_handle_get_fair_value_gaps,
    ),
]
