from dataclasses import dataclass
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .strategies import Strategy, Candle, Signal


@dataclass
class BacktestResult:
    strategy_config: dict
    metrics: dict
    trades: list
    equity_curve: list
    drawdowns: list
    candles: list
    signals: list


class BacktestEngine:
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

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> list[dict]:
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT timestamp, datetime, open, high, low, close, volume
            FROM candles
            WHERE symbol = %s AND timeframe = %s
        """
        params = [symbol, timeframe]

        if start_timestamp:
            query += " AND timestamp >= %s"
            params.append(start_timestamp)

        if end_timestamp:
            query += " AND timestamp <= %s"
            params.append(end_timestamp)

        query += " ORDER BY timestamp ASC"

        cur.execute(query, params)
        rows = cur.fetchall()

        cur.close()
        conn.close()

        return [dict(row) for row in rows]

    def run(
        self,
        strategy: Strategy,
        symbol: str,
        timeframe: str,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        quantity: int = 1
    ) -> BacktestResult:
        strategy.reset()

        candle_data = self.get_candles(symbol, timeframe, start_timestamp, end_timestamp)

        candles_out = []
        signals_out = []

        for row in candle_data:
            candle = Candle(
                timestamp=row["timestamp"],
                datetime=str(row["datetime"]),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"]
            )

            signal = strategy.on_candle(candle)
            strategy.process_signal(signal, candle, quantity)

            candles_out.append({
                "timestamp": candle.timestamp,
                "datetime": candle.datetime,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume
            })

            signals_out.append({
                "datetime": candle.datetime,
                "signal": signal.name,
                "price": candle.close
            })

        trades_out = [
            {
                "entry_time": t.entry_time,
                "entry_price": t.entry_price,
                "exit_time": t.exit_time,
                "exit_price": t.exit_price,
                "quantity": t.quantity,
                "pnl": round(t.pnl, 2),
                "pnl_percent": round(t.pnl_percent, 2)
            }
            for t in strategy.state.trades
        ]

        return BacktestResult(
            strategy_config=strategy.get_config(),
            metrics=strategy.get_metrics(),
            trades=trades_out,
            equity_curve=strategy.state.equity_curve,
            drawdowns=strategy.state.drawdowns,
            candles=candles_out,
            signals=signals_out
        )

    def get_available_data(self) -> list[dict]:
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT symbol, timeframe, COUNT(*) as candle_count,
                   MIN(datetime) as start_date, MAX(datetime) as end_date
            FROM candles
            GROUP BY symbol, timeframe
            ORDER BY symbol, timeframe
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [dict(row) for row in rows]
