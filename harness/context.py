"""
RunContext: the per-cycle scratchpad tool handlers get passed. Right now
that's just the candle cache (so 6 different tools calling get_candles on
the same symbol/timeframe within one cycle hit the data source once), but
it's the natural place to add a broker session, a request-scoped logger,
etc. later without changing every tool's signature again.
"""
import config
from tools import market_data


class RunContext:
    def __init__(self, symbol: str = ""):
        self._candle_cache: dict[tuple, object] = {}
        self.symbol = symbol  # default symbol for tools that need it

    def get_candles(self, symbol: str | None = None, timeframe: str = "HTF"):
        """Get candles for a symbol/timeframe, with fallback to ctx.symbol."""
        symbol = symbol or self.symbol
        if not symbol:
            return pd.DataFrame()  # empty → tools will error gracefully
        key = (symbol, timeframe)
        if key not in self._candle_cache:
            interval, lookback = (
                (config.HTF_INTERVAL, config.LOOKBACK_HTF) if timeframe == "HTF"
                else (config.LTF_INTERVAL, config.LOOKBACK_LTF)
            )
            self._candle_cache[key] = market_data.get_candles(symbol, interval, lookback)
        return self._candle_cache[key]
