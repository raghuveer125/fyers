from dataclasses import dataclass, field
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .strategies import Strategy, Candle, Signal, RSIStrategy, MACDStrategy, RSIMACDStrategy
from .strategies.rsi import RSIConfig
from .strategies.macd import MACDConfig


@dataclass
class SimulatorState:
    candles: list = field(default_factory=list)
    current_index: int = 0
    strategy: Optional[Strategy] = None
    symbol: str = ""
    timeframe: str = ""
    history: list = field(default_factory=list)


class LiveSimulator:
    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_user: str = "trader",
        db_password: str = "trader123",
        db_name: str = "fyers"
    ):
        self.db_config = {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_password,
            "dbname": db_name
        }
        self.sessions: dict[str, SimulatorState] = {}

    def create_session(
        self,
        session_id: str,
        symbol: str,
        timeframe: str,
        strategy_type: str,
        strategy_params: dict,
        initial_capital: float = 100000.0
    ) -> dict:
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT timestamp, datetime, open, high, low, close, volume
            FROM candles
            WHERE symbol = %s AND timeframe = %s
            ORDER BY timestamp ASC
        """, [symbol, timeframe])

        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            raise ValueError(f"No candles found for {symbol} {timeframe}")

        candles = [dict(row) for row in rows]

        if strategy_type == "RSI":
            config = RSIConfig(
                period=strategy_params.get("period", 14),
                overbought=strategy_params.get("overbought", 70.0),
                oversold=strategy_params.get("oversold", 30.0)
            )
            strategy = RSIStrategy(config=config, initial_capital=initial_capital)
        elif strategy_type == "MACD":
            config = MACDConfig(
                fast_period=strategy_params.get("fast_period", 12),
                slow_period=strategy_params.get("slow_period", 26),
                signal_period=strategy_params.get("signal_period", 9)
            )
            strategy = MACDStrategy(config=config, initial_capital=initial_capital)
        elif strategy_type == "RSI+MACD":
            rsi_config = RSIConfig(
                period=strategy_params.get("rsi_period", 14),
                overbought=strategy_params.get("rsi_overbought", 70.0),
                oversold=strategy_params.get("rsi_oversold", 30.0)
            )
            macd_config = MACDConfig(
                fast_period=strategy_params.get("macd_fast", 12),
                slow_period=strategy_params.get("macd_slow", 26),
                signal_period=strategy_params.get("macd_signal", 9)
            )
            strategy = RSIMACDStrategy(rsi_config=rsi_config, macd_config=macd_config, initial_capital=initial_capital)
        else:
            raise ValueError(f"Unknown strategy: {strategy_type}")

        state = SimulatorState(
            candles=candles,
            current_index=0,
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            history=[]
        )

        self.sessions[session_id] = state

        return {
            "session_id": session_id,
            "symbol": symbol,
            "timeframe": timeframe,
            "total_candles": len(candles),
            "strategy": strategy.get_config()
        }

    def step(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        state = self.sessions[session_id]

        if state.current_index >= len(state.candles):
            return {
                "status": "finished",
                "message": "All candles processed",
                "metrics": state.strategy.get_metrics(),
                "history": state.history
            }

        row = state.candles[state.current_index]
        candle = Candle(
            timestamp=row["timestamp"],
            datetime=str(row["datetime"]),
            open=row["open"],
            high=row["high"],
            low=row["low"],
            close=row["close"],
            volume=row["volume"]
        )

        signal = state.strategy.on_candle(candle)
        state.strategy.process_signal(signal, candle, quantity=1)

        rsi_value = None
        macd_line = None
        macd_signal = None
        macd_histogram = None

        if hasattr(state.strategy, 'rsi'):
            rsi_value = state.strategy.rsi.value
        if hasattr(state.strategy, 'macd'):
            macd_line = state.strategy.macd.macd_line
            macd_signal = state.strategy.macd.signal_line
            macd_histogram = state.strategy.macd.histogram

        step_data = {
            "index": state.current_index,
            "candle": {
                "timestamp": candle.timestamp,
                "datetime": candle.datetime,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume
            },
            "signal": signal.name,
            "position": state.strategy.state.position,
            "equity": round(state.strategy.state.equity, 2),
            "indicators": {
                "rsi": round(rsi_value, 2) if rsi_value is not None else None,
                "macd_line": round(macd_line, 2) if macd_line is not None else None,
                "macd_signal": round(macd_signal, 2) if macd_signal is not None else None,
                "macd_histogram": round(macd_histogram, 2) if macd_histogram is not None else None
            },
            "current_trade": None,
            "last_completed_trade": None
        }

        if state.strategy.state.current_trade:
            t = state.strategy.state.current_trade
            step_data["current_trade"] = {
                "entry_time": t.entry_time,
                "entry_price": t.entry_price
            }

        if state.strategy.state.trades:
            t = state.strategy.state.trades[-1]
            step_data["last_completed_trade"] = {
                "entry_time": t.entry_time,
                "entry_price": t.entry_price,
                "exit_time": t.exit_time,
                "exit_price": t.exit_price,
                "pnl": round(t.pnl, 2),
                "pnl_percent": round(t.pnl_percent, 2)
            }

        state.history.append(step_data)
        state.current_index += 1

        return {
            "status": "ok",
            "remaining": len(state.candles) - state.current_index,
            "total": len(state.candles),
            "step": step_data,
            "metrics": state.strategy.get_metrics()
        }

    def get_state(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        state = self.sessions[session_id]

        return {
            "session_id": session_id,
            "symbol": state.symbol,
            "timeframe": state.timeframe,
            "current_index": state.current_index,
            "total_candles": len(state.candles),
            "remaining": len(state.candles) - state.current_index,
            "metrics": state.strategy.get_metrics(),
            "history": state.history
        }

    def reset(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        state = self.sessions[session_id]
        state.current_index = 0
        state.history = []
        state.strategy.reset()

        return {
            "status": "ok",
            "message": "Session reset",
            "total_candles": len(state.candles)
        }

    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
