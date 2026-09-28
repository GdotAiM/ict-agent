"""
SMC Data Bridge - loads candle data from smc-icm-trading's engine outputs or TV CDP.
This bypasses yfinance entirely since Python SSL is broken on this machine.
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone


def get_candles_from_tv(symbol: str, interval: str) -> pd.DataFrame | None:
    """Fetch candles from TradingView CDP via smc-icm-trading's fetch_candles.cjs."""
    import subprocess, os, tempfile
    # Map symbol to smc-icm format — strip =X suffix only after the lookup key
    # is resolved; do NOT modify the lookup key itself (keep EURUSD=X for the map).
    sym = symbol.replace("=X", "")
    # Map interval to TV resolution
    tf_map = {"1h": "60", "15m": "15", "5m": "5", "1m": "1", "4h": "240", "1d": "D", "1w": "W", "15": "15", "5": "5", "1": "1", "60": "60", "240": "240"}
    resolution = tf_map.get(interval, interval)

    # Try multiple CDP ports (9222 = default, 9333 = dedicated TV instance)
    cdp_ports = [int(os.getenv("TV_CDP_PORT", "9222")), 9333]

    tmpfile = tempfile.mktemp(suffix=".json")
    for cdp_port in cdp_ports:
        try:
            result = subprocess.run(
                ["node", r"C:\Users\cash\smc-icm-trading\tools\tv-mcp\fetch_candles.cjs",
                 "--pair", sym, "--tf", interval, "--output", tmpfile],
                capture_output=True, text=True, timeout=15,
                env={**os.environ, "CDP_PORT": str(cdp_port)},
            )
            if result.returncode == 0 and os.path.exists(tmpfile):
                with open(tmpfile) as f:
                    raw = f.read().strip()
                if raw and not raw.startswith('{"error"'):
                    return _parse_candle_output(raw, interval, tf_map, symbol)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    return None


def _parse_candle_output(raw: str, interval: str, tf_map: dict, symbol: str) -> pd.DataFrame:
    """Parse candle JSON into DataFrame, with cross-symbol contamination guard."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    df = None
    if isinstance(parsed, list):
        if parsed and "time" in parsed[0]:
            df = pd.DataFrame(parsed)
            df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
            df.set_index("time", inplace=True)
    elif isinstance(parsed, dict):
        tfs = parsed.get("timeframes", {})
        tv_key = tf_map.get(interval, interval)
        if tv_key in tfs and "candles" in tfs[tv_key]:
            candles = tfs[tv_key]["candles"]
            df = pd.DataFrame(candles)
            if "time" in df.columns:
                df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
                df.set_index("time", inplace=True)

    if df is None or df.empty:
        return None

    # ── Cross-symbol contamination guard ──────────────────────
    _expected_ranges = {
        "EURUSD": (1.0, 1.5), "GBPUSD": (1.2, 1.6),
        "XAUUSD": (3000, 6000), "NAS100": (20000, 40000),
        "SPY": (600, 900), "USDOLLAR": (95, 120),
    }
    pair_key = symbol.replace("=X", "").upper()
    if pair_key in _expected_ranges:
        lo, hi = _expected_ranges[pair_key]
        closes = df["close"].values
        if len(closes) > 0:
            last_close = float(closes[-1])
            if last_close < lo or last_close > hi:
                print(f"[WARN] Contamination detected: {symbol.replace('=X','')}@{interval} returned close={last_close:.4f} "
                      f"outside expected [{lo}, {hi}] — discarding")
                return None
    # ── End guard ─────────────────────────────────────────────
    return df


def get_candles_from_engine(symbol: str, interval: str, lookback_days: int = 10) -> pd.DataFrame:
    """
    Load candle data from smc-icm-trading engine outputs.

    symbol: e.g., 'EURUSD', 'GBPUSD', 'XAUUSD', 'NAS100'
    interval: '1h', '15m', etc.
    Returns DataFrame with columns: open, high, low, close, volume
    """
    # Map symbol to smc-icm format
    symbol_map = {
        "EURUSD=X": "EURUSD",
        "GBPUSD=X": "GBPUSD",
        "XAUUSD": "XAUUSD",
        "NAS100": "NAS100",
        "SPY": "SPY",
    }
    pair = symbol_map.get(symbol, symbol.replace("=X", ""))

    # Try TV CDP first (real-time)
    tv_df = get_candles_from_tv(symbol, interval)
    if tv_df is not None and not tv_df.empty:
        return tv_df

    # Try engine outputs from smc-icm-trading
    smc_paths = [
        Path(r"C:\Users\cash\smc-icm-trading"),
        Path(r"C:\Users\cash\SMC-Liquidity-Hunter"),
    ]

    interval_map = {"1h": "1h", "15m": "15m", "5m": "5m", "1m": "1m", "4h": "4h", "1d": "1d", "1w": "1w"}
    tf_key = interval_map.get(interval, interval)

    for smc_path in smc_paths:
        # Try recent dates
        for days_back in range(7):
            date_str = (datetime.now(timezone.utc) - __import__('datetime').timedelta(days=days_back)).strftime("%Y-%m-%d")
            engine_file = smc_path / "shared" / date_str / pair / f"engine_{tf_key}.json"

            if engine_file.exists():
                try:
                    with open(engine_file) as f:
                        data = json.load(f)

                    # Extract candles from engine output
                    if "candles" in data:
                        candles = data["candles"]
                        df = pd.DataFrame(candles)
                        if "timestamp" in df.columns:
                            df["timestamp"] = pd.to_datetime(df["timestamp"])
                            df.set_index("timestamp", inplace=True)
                        return df

                    # Try raw candle data
                    if "raw_candles" in data:
                        candles = data["raw_candles"]
                        df = pd.DataFrame(candles)
                        return df

                except Exception as e:
                    continue

    # Fall back to mock data if no data found
    return _generate_mock_candles(symbol, interval, lookback_days)


def _generate_mock_candles(symbol: str, interval: str, lookback: str = "10d") -> pd.DataFrame:
    """Generate realistic mock candle data for testing.

    NOTE: This is SYNTHETIC data — the random walk is seeded with a stable
    CRC32 of the symbol name so results are reproducible across processes,
    but the prices are NOT real market prices. Any analysis built on this
    must be treated as pipeline validation only, not tradeable signal.
    """
    import numpy as np
    import zlib

    # Parse lookback to get days (handle "10d", "5d", etc.)
    try:
        days = int(lookback.replace("d", ""))
    except (ValueError, AttributeError):
        days = 10

    # Base price depending on symbol
    base_prices = {
        "EURUSD=X": 1.0850,
        "GBPUSD=X": 1.2650,
        "XAUUSD": 3350.0,
        "NAS100": 21500.0,
        "SPY": 580.0,
    }
    base = base_prices.get(symbol, 100.0)

    # Log once per process that we're in mock mode
    if not getattr(_generate_mock_candles, "_warned", False):
        _generate_mock_candles._warned = True
        print(f"[DATA-WARN] No live data source available — using SYNTHETIC mock candles "
              f"for {symbol}. Levels are NOT real prices.", file=__import__("sys").stderr)

    # Generate candles
    n_candles = days * 24 if interval == "1h" else days * 96  # 96 15m bars per day
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=n_candles, freq=interval)

    np.random.seed(zlib.crc32(symbol.upper().encode()) % 2**32)
    returns = np.random.randn(n_candles) * 0.001
    prices = base * (1 + np.cumsum(returns))

    # Create OHLCV
    df = pd.DataFrame({
        'open': prices + np.random.randn(n_candles) * base * 0.0001,
        'high': prices + abs(np.random.randn(n_candles)) * base * 0.0002,
        'low': prices - abs(np.random.randn(n_candles)) * base * 0.0002,
        'close': prices,
        'volume': np.random.randint(1000, 10000, n_candles)
    }, index=dates)

    return df
