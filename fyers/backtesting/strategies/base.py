from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class Signal(Enum):
    HOLD = 0
    BUY = 1
    SELL = -1


@dataclass
class Candle:
    timestamp: int
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Trade:
    entry_time: str
    entry_price: float
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    quantity: int = 1
    pnl: float = 0.0
    pnl_percent: float = 0.0

    def close(self, exit_time: str, exit_price: float):
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.pnl = (self.exit_price - self.entry_price) * self.quantity
        self.pnl_percent = ((self.exit_price - self.entry_price) / self.entry_price) * 100


@dataclass
class StrategyState:
    position: int = 0  # 0 = flat, 1 = long
    trades: list = field(default_factory=list)
    current_trade: Optional[Trade] = None
    equity: float = 100000.0
    initial_equity: float = 100000.0
    equity_curve: list = field(default_factory=list)
    max_equity: float = 100000.0
    drawdowns: list = field(default_factory=list)


class Strategy(ABC):
    def __init__(self, initial_capital: float = 100000.0):
        self.state = StrategyState(
            equity=initial_capital,
            initial_equity=initial_capital,
            max_equity=initial_capital
        )

    @abstractmethod
    def on_candle(self, candle: Candle) -> Signal:
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_config(self) -> dict:
        pass

    def process_signal(self, signal: Signal, candle: Candle, quantity: int = 1):
        if signal == Signal.BUY and self.state.position == 0:
            self.state.position = 1
            self.state.current_trade = Trade(
                entry_time=candle.datetime,
                entry_price=candle.close,
                quantity=quantity
            )

        elif signal == Signal.SELL and self.state.position == 1:
            self.state.position = 0
            if self.state.current_trade:
                self.state.current_trade.close(candle.datetime, candle.close)
                self.state.equity += self.state.current_trade.pnl
                self.state.trades.append(self.state.current_trade)
                self.state.current_trade = None

        self.state.equity_curve.append({
            "datetime": candle.datetime,
            "equity": self.state.equity
        })

        if self.state.equity > self.state.max_equity:
            self.state.max_equity = self.state.equity

        drawdown = ((self.state.max_equity - self.state.equity) / self.state.max_equity) * 100
        self.state.drawdowns.append({
            "datetime": candle.datetime,
            "drawdown": drawdown
        })

    def get_metrics(self) -> dict:
        if not self.state.trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "total_pnl_percent": 0.0,
                "avg_pnl": 0.0,
                "max_drawdown": 0.0,
                "final_equity": self.state.equity,
                "return_percent": 0.0
            }

        winning = [t for t in self.state.trades if t.pnl > 0]
        losing = [t for t in self.state.trades if t.pnl <= 0]
        total_pnl = sum(t.pnl for t in self.state.trades)
        max_dd = max(d["drawdown"] for d in self.state.drawdowns) if self.state.drawdowns else 0

        return {
            "total_trades": len(self.state.trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(self.state.trades)) * 100 if self.state.trades else 0,
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round((total_pnl / self.state.initial_equity) * 100, 2),
            "avg_pnl": round(total_pnl / len(self.state.trades), 2) if self.state.trades else 0,
            "max_drawdown": round(max_dd, 2),
            "final_equity": round(self.state.equity, 2),
            "return_percent": round(((self.state.equity - self.state.initial_equity) / self.state.initial_equity) * 100, 2)
        }
