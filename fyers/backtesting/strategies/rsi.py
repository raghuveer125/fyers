from dataclasses import dataclass
from typing import Optional
from collections import deque

from .base import Strategy, Signal, Candle, StrategyState


@dataclass
class RSIConfig:
    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0


class RSI:
    def __init__(self, config: RSIConfig = None):
        self.config = config or RSIConfig()
        self.gains = deque(maxlen=self.config.period)
        self.losses = deque(maxlen=self.config.period)
        self.prev_close: Optional[float] = None
        self.value: Optional[float] = None

    def update(self, close: float) -> Optional[float]:
        if self.prev_close is not None:
            change = close - self.prev_close
            gain = max(0, change)
            loss = max(0, -change)
            self.gains.append(gain)
            self.losses.append(loss)

            if len(self.gains) == self.config.period:
                avg_gain = sum(self.gains) / self.config.period
                avg_loss = sum(self.losses) / self.config.period

                if avg_loss == 0:
                    self.value = 100.0
                else:
                    rs = avg_gain / avg_loss
                    self.value = 100 - (100 / (1 + rs))

        self.prev_close = close
        return self.value

    def reset(self):
        self.gains.clear()
        self.losses.clear()
        self.prev_close = None
        self.value = None


class RSIStrategy(Strategy):
    def __init__(self, config: RSIConfig = None, initial_capital: float = 100000.0):
        super().__init__(initial_capital)
        self.config = config or RSIConfig()
        self.rsi = RSI(self.config)

    def on_candle(self, candle: Candle) -> Signal:
        rsi_value = self.rsi.update(candle.close)

        if rsi_value is None:
            return Signal.HOLD

        # BUY when RSI crosses below oversold level
        if rsi_value < self.config.oversold and self.state.position == 0:
            return Signal.BUY

        # SELL when RSI crosses above overbought level
        elif rsi_value > self.config.overbought and self.state.position == 1:
            return Signal.SELL

        return Signal.HOLD

    def reset(self):
        self.rsi.reset()
        self.state = StrategyState(
            equity=self.state.initial_equity,
            initial_equity=self.state.initial_equity,
            max_equity=self.state.initial_equity
        )

    def get_config(self) -> dict:
        return {
            "strategy": "RSI",
            "period": self.config.period,
            "overbought": self.config.overbought,
            "oversold": self.config.oversold
        }
