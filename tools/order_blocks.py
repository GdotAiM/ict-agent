"""
Order Blocks (OB): the last opposite-colored candle before a strong
displacement move that breaks structure — read as the footprint of the
institutional order that fueled the move.
"""
import pandas as pd
from .structure import get_market_structure
from harness.plugin import ToolPlugin


def get_order_blocks(df: pd.DataFrame, displacement_atr_mult: float = 1.5,
                      max_results: int = 5) -> list:
    tr = (df["high"] - df["low"])
    atr = tr.rolling(14).mean()

    obs = []
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values

    for i in range(15, len(df)):
        body = c[i] - o[i]
        is_displacement = abs(body) > (atr.iloc[i] * displacement_atr_mult if not pd.isna(atr.iloc[i]) else float("inf"))
        if not is_displacement:
            continue

        if body > 0:
            # bullish displacement -> find last down-close candle before it
            j = i - 1
            while j > 0 and c[j] >= o[j]:
                j -= 1
            if j >= 0 and c[j] < o[j]:
                obs.append({
                    "type": "bullish",
                    "top": float(o[j]),
                    "bottom": float(l[j]),
                    "formed_at": str(df.index[j]),
                    "displacement_at": str(df.index[i]),
                })
        else:
            # bearish displacement -> find last up-close candle before it
            j = i - 1
            while j > 0 and c[j] <= o[j]:
                j -= 1
            if j >= 0 and c[j] > o[j]:
                obs.append({
                    "type": "bearish",
                    "top": float(h[j]),
                    "bottom": float(o[j]),
                    "formed_at": str(df.index[j]),
                    "displacement_at": str(df.index[i]),
                })

    last_close = float(c[-1])
    unmitigated = [ob for ob in obs if not (ob["bottom"] <= last_close <= ob["top"])]
    return (unmitigated[-max_results:] if unmitigated else obs[-max_results:])


def _handle_get_order_blocks(tool_input: dict, ctx) -> dict:
    df = ctx.get_candles(tool_input["symbol"], tool_input["timeframe"])
    return {"order_blocks": get_order_blocks(df)}


PLUGINS = [
    ToolPlugin(
        name="get_order_blocks",
        description="Returns unmitigated bullish/bearish order blocks on the given symbol/timeframe.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["HTF", "LTF"]},
            },
            "required": ["symbol", "timeframe"],
        },
        handler=_handle_get_order_blocks,
    ),
]
