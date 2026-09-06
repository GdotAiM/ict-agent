"""
Execution tool: places bracket orders (entry + stop + target) on Alpaca's
paper trading endpoint. This is the ONLY file that touches real order
placement — everything above this is analysis only.
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, TimeInForce

import config
from harness.plugin import ToolPlugin

_client = None


def _get_client() -> TradingClient:
    global _client
    if _client is None:
        if not config.ALPACA_API_KEY or not config.ALPACA_SECRET_KEY:
            raise RuntimeError("Alpaca API keys not set — check your .env")
        _client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY,
                                 paper=config.ALPACA_PAPER)
    return _client


def get_account_info() -> dict:
    acct = _get_client().get_account()
    return {
        "equity": float(acct.equity),
        "buying_power": float(acct.buying_power),
        "cash": float(acct.cash),
    }


def get_open_positions() -> list:
    positions = _get_client().get_all_positions()
    return [{"symbol": p.symbol, "qty": p.qty, "side": p.side,
              "avg_entry_price": p.avg_entry_price,
              "unrealized_pl": p.unrealized_pl} for p in positions]


def calc_position_size(equity: float, entry: float, stop: float,
                        risk_pct: float) -> int:
    risk_amount = equity * (risk_pct / 100)
    per_share_risk = abs(entry - stop)
    if per_share_risk <= 0:
        return 0
    return max(int(risk_amount / per_share_risk), 0)


def place_paper_trade(symbol: str, direction: str, entry: float,
                       stop: float, target: float, risk_pct: float = None) -> dict:
    """
    direction: 'long' or 'short'
    Places a market order with attached stop-loss and take-profit
    (an Alpaca bracket order). Sizes the position off account equity and
    RISK_PER_TRADE_PCT unless risk_pct is overridden.
    """
    risk_pct = risk_pct or config.RISK_PER_TRADE_PCT
    acct = get_account_info()
    qty = calc_position_size(acct["equity"], entry, stop, risk_pct)
    if qty <= 0:
        return {"placed": False, "reason": "calculated position size was 0"}

    side = OrderSide.BUY if direction == "long" else OrderSide.SELL

    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.GTC,
        order_class="bracket",
        take_profit=TakeProfitRequest(limit_price=round(target, 4)),
        stop_loss=StopLossRequest(stop_price=round(stop, 4)),
    )
    result = _get_client().submit_order(order)
    return {
        "placed": True,
        "order_id": str(result.id),
        "symbol": symbol,
        "direction": direction,
        "qty": qty,
        "entry_ref": entry,
        "stop": stop,
        "target": target,
    }


def _handle_get_account_info(tool_input: dict, ctx) -> dict:
    return get_account_info()


def _handle_place_paper_trade(tool_input: dict, ctx) -> dict:
    from memory import store  # local import: avoids a circular import at module load
    result = place_paper_trade(
        symbol=tool_input["symbol"], direction=tool_input["direction"],
        entry=tool_input["entry"], stop=tool_input["stop"],
        target=tool_input["target"],
    )
    if result.get("placed"):
        store.log_trade(
            symbol=tool_input["symbol"], direction=tool_input["direction"],
            entry=tool_input["entry"], stop=tool_input["stop"],
            target=tool_input["target"], qty=result["qty"],
            order_id=result["order_id"],
        )
    return result


PLUGINS = [
    ToolPlugin(
        name="get_account_info",
        description="Returns paper account equity, cash, and buying power.",
        input_schema={"type": "object", "properties": {}},
        handler=_handle_get_account_info,
    ),
    ToolPlugin(
        name="place_paper_trade",
        description="Places a bracket paper trade (market entry + stop + target) sized by account risk. Only call this once confluence per the instructions is met.",
        input_schema={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "direction": {"type": "string", "enum": ["long", "short"]},
                "entry": {"type": "number"},
                "stop": {"type": "number"},
                "target": {"type": "number"},
            },
            "required": ["symbol", "direction", "entry", "stop", "target"],
        },
        handler=_handle_place_paper_trade,
    ),
]
