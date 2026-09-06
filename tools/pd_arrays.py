"""
PD Array: premium/discount relative to the equilibrium (50%) of the current
dealing range. ICT rule of thumb — buy from discount, sell from premium.
"""
import pandas as pd
from harness.plugin import ToolPlugin


def get_pd_array(df: pd.DataFrame, range_bars: int = 50) -> dict:
    window = df.tail(range_bars)
    high = float(window["high"].max())
    low = float(window["low"].min())
    eq = (high + low) / 2
    last_close = float(df["close"].iloc[-1])

    if last_close > eq:
        zone = "premium"
        pct_into_zone = (last_close - eq) / (high - eq) * 100 if high != eq else 0
    else:
        zone = "discount"
        pct_into_zone = (eq - last_close) / (eq - low) * 100 if eq != low else 0

    return {
        "range_high": high,
        "range_low": low,
        "equilibrium": eq,
        "current_price": last_close,
        "zone": zone,
        "pct_into_zone": round(pct_into_zone, 1),
    }


def _handle_get_pd_array(tool_input: dict, ctx) -> dict:
    df = ctx.get_candles(tool_input["symbol"], tool_input["timeframe"])
    return get_pd_array(df)


PLUGINS = [
    ToolPlugin(
        name="get_pd_array",
        description="Returns the current dealing range's equilibrium, and whether price is in premium or discount.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "timeframe": {"type": "string", "enum": ["HTF", "LTF"]},
            },
            "required": ["symbol", "timeframe"],
        },
        handler=_handle_get_pd_array,
    ),
]
