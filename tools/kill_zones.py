"""
Kill zones: the ICT session windows where setups carry the highest
probability (institutional participation is highest).
"""
from datetime import datetime, timezone
from config import KILL_ZONES_UTC
from harness.plugin import ToolPlugin


def get_kill_zone(now: datetime = None) -> dict:
    now = now or datetime.now(timezone.utc)
    hour = now.hour
    active = [name for name, (start, end) in KILL_ZONES_UTC.items()
              if start <= hour < end]
    return {
        "utc_time": now.strftime("%Y-%m-%d %H:%M UTC"),
        "active_kill_zones": active,
        "in_kill_zone": len(active) > 0,
    }


def _handle_get_kill_zone(tool_input: dict, ctx) -> dict:
    return get_kill_zone()


PLUGINS = [
    ToolPlugin(
        name="get_kill_zone",
        description="Returns whether the current UTC time falls inside an ICT kill zone (Asian/London/NY AM/NY PM).",
        input_schema={"type": "object", "properties": {}},
        handler=_handle_get_kill_zone,
    ),
]
