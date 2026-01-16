from typing import Optional

from .base import Strategy, Signal, Candle, StrategyState
from .rsi import RSI, RSIConfig
from .macd import MACD, MACDConfig


class RSIMACDStrategy(Strategy):
    def __init__(
        self,
        rsi_config: RSIConfig = None,
        macd_config: MACDConfig = None,
        initial_capital: float = 100000.0
    ):
        super().__init__(initial_capital)
        self.rsi_config = rsi_config or RSIConfig()
        self.macd_config = macd_config or MACDConfig()
        self.rsi = RSI(self.rsi_config)
        self.macd = MACD(self.macd_config)
        self.prev_histogram: Optional[float] = None

    def on_candle(self, candle: Candle) -> Signal:
        rsi_value = self.rsi.update(candle.close)
        macd_line, signal_line, histogram = self.macd.update(candle.close)

        if rsi_value is None or histogram is None or self.prev_histogram is None:
            self.prev_histogram = histogram
            return Signal.HOLD

        # BUY: RSI oversold OR MACD bullish crossover
        rsi_oversold = rsi_value < self.rsi_config.oversold
        macd_bullish = self.prev_histogram < 0 and histogram >= 0

        if (rsi_oversold or macd_bullish) and self.state.position == 0:
            self.prev_histogram = histogram
            return Signal.BUY

        # SELL: RSI overbought OR MACD bearish crossover
        rsi_overbought = rsi_value > self.rsi_config.overbought
        macd_bearish = self.prev_histogram > 0 and histogram <= 0

        if (rsi_overbought or macd_bearish) and self.state.position == 1:
            self.prev_histogram = histogram
            return Signal.SELL

        self.prev_histogram = histogram
        return Signal.HOLD

    def reset(self):
        self.rsi.reset()
        self.macd.reset()
        self.prev_histogram = None
        self.state = StrategyState(
            equity=self.state.initial_equity,
            initial_equity=self.state.initial_equity,
            max_equity=self.state.initial_equity
        )

    def get_config(self) -> dict:
        return {
            "strategy": "RSI+MACD",
            "rsi_period": self.rsi_config.period,
            "rsi_overbought": self.rsi_config.overbought,
            "rsi_oversold": self.rsi_config.oversold,
            "macd_fast": self.macd_config.fast_period,
            "macd_slow": self.macd_config.slow_period,
            "macd_signal": self.macd_config.signal_period
        }
