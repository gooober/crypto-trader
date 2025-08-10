from dataclasses import dataclass
from typing import Optional, List, Dict
import time
import pandas as pd

@dataclass
class Bracket:
    stop: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_atr_mult: Optional[float] = 1.0  # default per spec

@dataclass
class PaperOrder:
    ts: float
    symbol: str
    side: str   # BUY/SELL
    qty: float
    entry: float
    fees_bps: float
    slippage_bps: float
    bracket: Bracket
    status: str = "filled"
    exit_price: Optional[float] = None
    pnl_usd: Optional[float] = None

class PaperEngine:
    def __init__(self, starting_cash_usd: float = 10000.0):
        self.cash = starting_cash_usd
        self.positions: Dict[str, float] = {}  # symbol -> qty (net)
        self.orders: List[PaperOrder] = []
        self.realized_pnl = 0.0
        self.daily_loss_limit_pct = 0.02
        self.max_trades_per_day = 20
        self.trades_today = 0
        self.last_reset_day = time.strftime("%Y-%m-%d")

    def _reset_if_new_day(self):
        today = time.strftime("%Y-%m-%d")
        if today != self.last_reset_day:
            self.trades_today = 0
            self.last_reset_day = today

    def can_trade(self) -> bool:
        self._reset_if_new_day()
        if self.realized_pnl < -self.daily_loss_limit_pct * self.cash:
            return False
        if self.trades_today >= self.max_trades_per_day:
            return False
        return True

    def place(self, symbol: str, side: str, qty: float, price: float, fees_bps: float, slippage_bps: float, bracket: Bracket) -> PaperOrder:
        if not self.can_trade():
            raise RuntimeError("Daily guardrails reached (loss limit or max trades).")
        adj = (1 + slippage_bps/10000.0) if side == "BUY" else (1 - slippage_bps/10000.0)
        fill = price * adj
        fee = fill * qty * (fees_bps/10000.0)
        cost = fill * qty + fee if side == "BUY" else -(fill * qty - fee)
        self.cash -= cost
        self.positions[symbol] = self.positions.get(symbol, 0.0) + (qty if side == "BUY" else -qty)

        order = PaperOrder(time.time(), symbol, side, qty, fill, fees_bps, slippage_bps, bracket)
        self.orders.append(order)
        self.trades_today += 1
        return order

    def close_position(self, idx: int, price: float):
        order = self.orders[idx]
        if order.status != "filled":
            return
        qty = order.qty if order.side == "BUY" else -order.qty
        pnl = (price - order.entry) * qty
        fee = price * abs(qty) * (order.fees_bps/10000.0)
        pnl -= fee
        order.exit_price = price
        order.pnl_usd = pnl
        order.status = "closed"
        self.realized_pnl += pnl
        proceeds = price * (-qty) - fee
        self.cash += proceeds

    def to_frame(self) -> pd.DataFrame:
        rows = []
        for i, o in enumerate(self.orders[-200:][::-1]):
            rows.append({
                "i": len(self.orders)-1 - i,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(o.ts)),
                "symbol": o.symbol,
                "side": o.side,
                "qty": round(o.qty, 8),
                "entry": round(o.entry, 2),
                "exit": round(o.exit_price, 2) if o.exit_price else None,
                "pnl_usd": round(o.pnl_usd, 2) if o.pnl_usd is not None else None,
                "status": o.status,
                "stop": o.bracket.stop,
                "tp": o.bracket.take_profit,
                "trail_atr": o.bracket.trailing_atr_mult,
            })
        return pd.DataFrame(rows)
