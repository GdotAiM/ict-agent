"""
SessionState — cross-cycle persistent state for the ICT agent.

Tracks per-symbol metadata that survives between `python main.py` invocations:
  - Last known bias and decision trajectory
  - Consecutive NO_SETUP / WATCH streaks
  - Time of last scan (for hysteresis checks)

Used by the MAG context builder so Stage 1 can see not just semantic recall
but also the agent's own recent decision pattern on this symbol.
"""
from __future__ import annotations
import json
import os
import time
import config


class SessionState:
    def __init__(self, path: str | None = None) -> None:
        self._path = path or os.path.join(
            os.path.dirname(os.path.abspath(config.__file__)),
            config.SESSION_STATE_PATH,
        )
        self._data: dict = {}
        self.load()

    # ---- persistence ------------------------------------------------------
    def load(self) -> None:
        if os.path.exists(self._path):
            try:
                with open(self._path) as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def save(self) -> None:
        try:
            with open(self._path, "w") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    # ---- per-symbol access ------------------------------------------------
    def _symbol_key(self, symbol: str) -> str:
        return symbol.replace("/", "_").replace("=", "_X")

    def get_bias(self, symbol: str) -> str | None:
        key = self._symbol_key(symbol)
        entry = self._data.get(key, {})
        return entry.get("last_bias")

    def get_decision(self, symbol: str) -> str | None:
        key = self._symbol_key(symbol)
        entry = self._data.get(key, {})
        return entry.get("last_decision")

    def get_streak(self, symbol: str, decision: str = "no_setup") -> int:
        """Count consecutive non-TRADE decisions ending at the most recent."""
        key = self._symbol_key(symbol)
        entry = self._data.get(key, {})
        streaks = entry.get("streaks", {})
        return streaks.get(decision, 0)

    def get_last_scan_ts(self, symbol: str) -> float | None:
        key = self._symbol_key(symbol)
        entry = self._data.get(key, {})
        ts = entry.get("last_scan_ts")
        return float(ts) if ts else None

    def update(self, symbol: str, bias: str, decision: str) -> None:
        key = self._symbol_key(symbol)
        now = time.time()
        if key not in self._data:
            self._data[key] = {"last_bias": None, "last_decision": None,
                               "streaks": {}, "last_scan_ts": None}
        entry = self._data[key]

        prev_decision = entry.get("last_decision")
        # Update streak counter
        if decision == "trade":
            entry["streaks"] = {}  # reset all streaks on a trade
        elif decision != prev_decision:
            # Switched to a new non-trade decision — start/count its streak
            entry["streaks"][decision] = 1
        else:
            entry["streaks"][decision] = entry["streaks"].get(decision, 0) + 1

        entry["last_bias"] = bias
        entry["last_decision"] = decision
        entry["last_scan_ts"] = now
        self.save()

    # ---- human-readable summary for prompts -------------------------------
    def build_summary(self, symbol: str) -> str:
        """Compact text suitable for injection into Stage 1 prompt."""
        key = self._symbol_key(symbol)
        entry = self._data.get(key, {})
        if not entry:
            return ""

        lines = []
        bias = entry.get("last_bias")
        decision = entry.get("last_decision")
        streak = entry.get("streaks", {})
        ts = entry.get("last_scan_ts")

        if bias:
            lines.append(f"Last known bias: {bias}")
        if decision:
            lines.append(f"Last decision: {decision}")
        no_setup = streak.get("no_setup", 0)
        watch = streak.get("watch", 0)
        if no_setup:
            lines.append(f"No-setup streak: {no_setup} consecutive")
        if watch:
            lines.append(f"Watch streak: {watch} consecutive")
        if ts:
            elapsed = int(time.time() - ts)
            mins = elapsed // 60
            hours = mins // 60
            if hours > 0:
                lines.append(f"Last scan: {hours}h{mins % 60}m ago")
            else:
                lines.append(f"Last scan: {mins}m ago")

        return " | ".join(lines) if lines else ""


# Module-level singleton loaded once per process
_state_cache: SessionState | None = None


def get_session_state(path: str | None = None) -> SessionState:
    global _state_cache
    if _state_cache is None or path:
        _state_cache = SessionState(path)
    return _state_cache
