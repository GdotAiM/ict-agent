"""
Power of 3 Phase Detection: Accumulation → Manipulation → Distribution.

ICT teaches that each session (London, NY AM, NY PM) follows a 3-phase
pattern:
  1. ACCUMULATION: Price ranges, building liquidity on both sides
  2. MANIPULATION: A false move in the opposite direction of intended bias
     (Judas swing) to trap retail traders
  3. DISTRIBUTION: The real move in the intended direction

This module detects which phase we're likely in based on time-of-day and
price action patterns.
"""
from datetime import datetime, timezone, timedelta


# Kill zone to phase mapping (ICT's standard session dynamics)
SESSION_PHASE_MAP = {
    "asian": {"primary": "accumulation", "description": "Range-building, low volatility"},
    "london": {"primary": "manipulation", "description": "Often creates false moves"},
    "ny_am": {"primary": "distribution", "description": "Main directional move"},
    "ny_pm": {"primary": "distribution", "description": "Continuation or reversal"},
}


def detect_power_of_3_phase(now: datetime = None) -> dict:
    """
    Determine the current Power of 3 phase based on UTC time.

    Returns dict with:
      - phase: 'accumulation', 'manipulation', 'distribution', 'unknown'
      - session: current kill zone name
      - confidence: 'high', 'medium', 'low'
      - description: ICT rationale
    """
    now = now or datetime.now(timezone.utc)
    hour = now.hour

    # Determine current session
    if 0 <= hour < 4:
        session = "asian"
    elif 7 <= hour < 10:
        session = "london"
    elif 12 <= hour < 15:
        session = "ny_am"
    elif 18 <= hour < 20:
        session = "ny_pm"
    else:
        session = "outside"

    phase_info = SESSION_PHASE_MAP.get(session, {"primary": "unknown", "description": "Outside high-probability windows"})

    # Confidence based on how well we align with session boundaries
    if session == "outside":
        confidence = "low"
    elif session == "asian":
        confidence = "medium"  # Asian can be choppy
    else:
        confidence = "high"

    return {
        "phase": phase_info["primary"],
        "session": session,
        "confidence": confidence,
        "description": phase_info["description"],
        "utc_time": now.strftime("%Y-%m-%d %H:%M UTC"),
    }


def detect_session_phase_from_price(df, current_hour: int = None) -> dict:
    """
    Advanced phase detection using price action patterns.

    Detects accumulation (tight range), manipulation (false break),
    and distribution (trend continuation) based on recent candle behavior.
    """
    if len(df) < 10:
        return {"phase": "unknown", "reason": "insufficient data"}

    recent = df.tail(10)
    range_size = float(recent["high"].max() - recent["low"].min())
    avg_body = float(recent["close"].abs().diff().mean())

    # Accumulation: tight range, small bodies
    if range_size < avg_body * 2:
        phase = "accumulation"
        reason = "Tight range with small bodies — building liquidity"
    # Manipulation: large wick opposite to trend
    elif recent["high"].iloc[-1] > recent["close"].iloc[-1] * 1.02:
        phase = "manipulation"
        reason = "Upper wick rejection — possible bearish manipulation"
    elif recent["low"].iloc[-1] < recent["close"].iloc[-1] * 0.98:
        phase = "manipulation"
        reason = "Lower wick rejection — possible bullish manipulation"
    else:
        phase = "distribution"
        reason = "Sustained directional movement — distribution phase"

    return {"phase": phase, "reason": reason, "hour": current_hour or datetime.now(timezone.utc).hour}


PLUGINS = []  # No tool plugin yet — phase detection used internally by prompts


def get_power_of_3_status(now: datetime = None) -> dict:
    """Public API for getting current Power of 3 status."""
    return detect_power_of_3_phase(now)
