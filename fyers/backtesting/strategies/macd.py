from dataclasses import dataclass
from typing import Optional

from .base import Strategy, Signal, Candle, StrategyState


@dataclass
class MACDConfig:
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9


class EMA:
    def __init__(self, period: int):
        self.period = period
        self.multiplier = 2 / (period + 1)
        self.value: Optional[float] = None
        self.count = 0
        self.sum = 0.0

    def update(self, price: float) -> Optional[float]:
        if self.value is None:
            self.sum += price
            self.count += 1
            if self.count == self.period:
                self.value = self.sum / self.period
        else:
            self.value = (price - self.value) * self.multiplier + self.value
        return self.value

    def reset(self):
        self.value = None
        self.count = 0
        self.sum = 0.0


class MACD:
    def __init__(self, config: MACDConfig = None):
        self.config = config or MACDConfig()
        self.fast_ema = EMA(self.config.fast_period)
        self.slow_ema = EMA(self.config.slow_period)
        self.signal_ema = EMA(self.config.signal_period)
        self.macd_line: Optional[float] = None
        self.signal_line: Optional[float] = None
        self.histogram: Optional[float] = None

    def update(self, close: float) -> tuple[Optional[float], Optional[float], Optional[float]]:
        fast = self.fast_ema.update(close)
        slow = self.slow_ema.update(close)

        if fast is not None and slow is not None:
            self.macd_line = fast - slow
            self.signal_line = self.signal_ema.update(self.macd_line)

            if self.signal_line is not None:
                self.histogram = self.macd_line - self.signal_line

        return self.macd_line, self.signal_line, self.histogram

    def reset(self):
        self.fast_ema.reset()
        self.slow_ema.reset()
        self.signal_ema.reset()
        self.macd_line = None
        self.signal_line = None
        self.histogram = None


class MACDStrategy(Strategy):
    def __init__(self, config: MACDConfig = None, initial_capital: float = 100000.0):
        super().__init__(initial_capital)
        self.config = config or MACDConfig()
        self.macd = MACD(self.config)
        self.prev_histogram: Optional[float] = None

    def on_candle(self, candle: Candle) -> Signal:
        macd_line, signal_line, histogram = self.macd.update(candle.close)

        if histogram is None or self.prev_histogram is None:
            self.prev_histogram = histogram
            return Signal.HOLD

        # BUY: histogram crosses above zero (bullish crossover)
        if self.prev_histogram < 0 and histogram >= 0 and self.state.position == 0:
            self.prev_histogram = histogram
            return Signal.BUY

        # SELL: histogram crosses below zero (bearish crossover)
        if self.prev_histogram > 0 and histogram <= 0 and self.state.position == 1:
            self.prev_histogram = histogram
            return Signal.SELL

        self.prev_histogram = histogram
        return Signal.HOLD

    def reset(self):
        self.macd.reset()
        self.prev_histogram = None
        self.state = StrategyState(
            equity=self.state.initial_equity,
            initial_equity=self.state.initial_equity,
            max_equity=self.state.initial_equity
        )

    def get_config(self) -> dict:
        return {
            "strategy": "MACD",
            "fast_period": self.config.fast_period,
            "slow_period": self.config.slow_period,
            "signal_period": self.config.signal_period
        }
