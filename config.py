"""
Central config for the ICT Agent.
Everything here is a knob you'll want to tune per symbol/session.
"""
import os
from dotenv import load_dotenv

# Explicitly load .env with override to ensure fresh values
load_dotenv(override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# Also check for ANTHROPIC_AUTH_TOKEN (Claude Code internal token)
if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "sk-ant-dummy":
    ANTHROPIC_AUTH_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
    if ANTHROPIC_AUTH_TOKEN:
        ANTHROPIC_API_KEY = ANTHROPIC_AUTH_TOKEN
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").lower() == "true"

# LLM component
MODEL = os.getenv("ICT_AGENT_MODEL", "claude-sonnet-5")
MAX_TOOL_ITERATIONS = 6

# LLM sampling controls
LLM_TEMPERATURE = float(os.getenv("ICT_LLM_TEMPERATURE", "0.2"))
LLM_TOP_P = float(os.getenv("ICT_LLM_TOP_P", "0.9"))
LLM_FREQUENCY_PENALTY = float(os.getenv("ICT_LLM_FREQUENCY_PENALTY", "0.0"))

# Token budgets (hard stops to prevent runaway stages)
TOKEN_BUDGET_PER_STAGE = int(os.getenv("ICT_TOKEN_BUDGET_PER_STAGE", "50000"))
TOKEN_BUDGET_PER_CYCLE = int(os.getenv("ICT_TOKEN_BUDGET_PER_CYCLE", "100000"))

# Message history — bounded sliding window per stage
MAX_MESSAGE_WINDOW = int(os.getenv("ICT_MAX_MESSAGE_WINDOW", "10"))

# Cross-cycle session state persistence
SESSION_STATE_PATH = os.getenv("ICT_SESSION_STATE_PATH", ".session_state.json")

# Prompt-chaining / gate-check controls (Udacity Output Validation)
# How many times a failed stage may be retried with the failure reason
# injected back into the prompt before the chain hard-stops.
GATE_MAX_RETRIES = int(os.getenv("ICT_GATE_MAX_RETRIES", "2"))
# If True, on final failure after retries the chain stops with no_setup.
# If False, the chain continues but marks the stage as degraded.
GATE_HARD_STOP_ON_EXHAUST = os.getenv("ICT_GATE_HARD_STOP", "true").lower() == "true"

# Watchlist — keep it small while you validate the loop
WATCHLIST = os.getenv("ICT_WATCHLIST", "EURUSD=X,GBPUSD=X,SPY").split(",")

# The instrument the video-grounded/forward prompt sets were written
# against (NQ continuous). Any symbol not containing this string triggers
# the 06_multi_instrument stage in agent/prompt_set_runner.py.
PROMPT_SET_NATIVE_INSTRUMENT = os.getenv("ICT_PROMPT_SET_NATIVE_INSTRUMENT", "NQ")

# Timeframes used for top-down analysis (yfinance interval strings)
HTF_INTERVAL = "1h"     # bias timeframe
LTF_INTERVAL = "15m"    # entry timeframe
LOOKBACK_HTF = "10d"
LOOKBACK_LTF = "5d"

# Risk
RISK_PER_TRADE_PCT = 0.5      # % of account equity risked per trade
MIN_RR = 2.0                  # minimum reward:risk the agent will accept
MAX_OPEN_POSITIONS = 3

# Time-weighted risk adjustment
# Multipliers applied based on kill zone (higher = more conviction window)
KILL_ZONE_RISK_MULT = {
    "ny_am": 1.5,    # Highest conviction — main institutional session
    "london": 1.3,   # Second highest — European overlap
    "ny_pm": 1.2,    # Moderate — afternoon extension
    "asian": 0.7,    # Lower conviction — range-bound typically
    "outside": 0.5,  # Lowest — avoid trading unless exceptional
}

# Kill zones (UTC hours, ICT's standard windows — adjust for DST if needed)
KILL_ZONES_UTC = {
    "asian":   (0, 4),
    "london":  (7, 10),
    "ny_am":   (12, 15),
    "ny_pm":   (18, 20),
}

# Where the memory DB lives
DB_PATH = os.getenv("ICT_AGENT_DB", "ict_agent.db")

CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
