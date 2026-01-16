import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime

import websocket
from dotenv import load_dotenv
from kafka import KafkaProducer

# --------------- LOGGING ---------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

# --------------- ENV & CONFIG ---------------
load_dotenv()
SYMBOLS_FILE = os.getenv("BINANCE_SYMBOLS_FILE", "symbols_crypto.json")
BINANCE_STREAM_BASE = os.getenv("BINANCE_STREAM_BASE", "wss://stream.binance.com:9443/stream?streams=")
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TIMEFRAMES = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

# --------------- LOAD SYMBOLS ---------------
def load_symbols():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = SYMBOLS_FILE if os.path.isabs(SYMBOLS_FILE) else os.path.join(base_dir, SYMBOLS_FILE)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("symbols_crypto.json must contain a JSON array of symbols")
        symbols = [s.strip() for s in data if isinstance(s, str) and s.strip()]
        if not symbols:
            raise ValueError("symbols_crypto.json is empty")
        return symbols
    except Exception as e:
        raise RuntimeError(f"Failed to load symbols from {SYMBOLS_FILE}: {e}")

symbols = load_symbols()
stream_symbols = [s.lower() for s in symbols]

# --------------- KAFKA PRODUCER ---------------
producer = KafkaProducer(
    bootstrap_servers=[BOOTSTRAP_SERVERS],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8") if k else None,
)

# --------------- CANDLE BUILDER ---------------
class CandleBuilder:
    def __init__(self, symbol, timeframe_seconds, timeframe_name):
        self.symbol = symbol
        self.timeframe_seconds = timeframe_seconds
        self.timeframe_name = timeframe_name
        self.current_candle = None
        self.candle_start_time = None

    def get_candle_start_time(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        if self.timeframe_seconds == 86400:  # 1 day
            return datetime(dt.year, dt.month, dt.day).timestamp()
        elif self.timeframe_seconds % 3600 == 0:  # hourly multiples (1h, 4h, etc.)
            hours = self.timeframe_seconds // 3600
            hour_slot = (dt.hour // hours) * hours
            return datetime(dt.year, dt.month, dt.day, hour_slot).timestamp()
        else:  # Minutes
            minutes = self.timeframe_seconds // 60
            minute_slot = (dt.minute // minutes) * minutes
            return datetime(dt.year, dt.month, dt.day, dt.hour, minute_slot).timestamp()

    def process_trade(self, price, qty, timestamp):
        try:
            if price is None or qty is None or timestamp is None:
                return None

            candle_start = self.get_candle_start_time(timestamp)

            # New candle
            if self.current_candle is None or candle_start != self.candle_start_time:
                completed_candle = None
                if self.current_candle is not None:
                    completed_candle = self.current_candle.copy()
                    completed_candle["closed"] = True

                self.candle_start_time = candle_start
                self.current_candle = {
                    "symbol": self.symbol,
                    "timeframe": self.timeframe_name,
                    "timestamp": int(candle_start),
                    "datetime": datetime.fromtimestamp(candle_start).isoformat(),
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 0.0,
                    "closed": False,
                }
                # add first trade volume
                self.current_candle["volume"] += qty
                return completed_candle

            # Update current candle
            self.current_candle["high"] = max(self.current_candle["high"], price)
            self.current_candle["low"] = min(self.current_candle["low"], price)
            self.current_candle["close"] = price
            self.current_candle["volume"] += qty
            return None

        except Exception as e:
            log.error(f"Error processing trade for {self.symbol} {self.timeframe_name}: {e}")
            return None

# --------------- BUILDERS ---------------
candle_builders = defaultdict(dict)
for symbol in symbols:
    symbol_upper = symbol.upper()
    for tf_name, tf_seconds in TIMEFRAMES.items():
        candle_builders[symbol_upper][tf_name] = CandleBuilder(symbol_upper, tf_seconds, tf_name)

# --------------- KAFKA PUBLISH ---------------
def publish_candle_to_kafka(candle):
    try:
        symbol = candle["symbol"].replace(":", "_").replace("-", "_")
        timeframe = candle["timeframe"]
        topic = f"candles_BINANCE_{symbol}"

        producer.send(
            topic,
            key=timeframe,
            value=candle,
        )
        log.info(
            f"📊 Candle published to {topic}: tf={timeframe} O={candle['open']:.2f} H={candle['high']:.2f} L={candle['low']:.2f} C={candle['close']:.2f} V={candle['volume']:.4f}"
        )
    except Exception as e:
        log.error(f"Error publishing candle: {e}")

# --------------- WEBSOCKET HANDLERS ---------------
def build_stream_url(symbols_lower):
    streams = [f"{s}@aggTrade" for s in symbols_lower]
    return BINANCE_STREAM_BASE + "/".join(streams)


def on_message(ws, message):
    try:
        payload = json.loads(message)
        data = payload.get("data", {})
        symbol = data.get("s")
        price = data.get("p")
        qty = data.get("q")
        ts_ms = data.get("T")

        if not symbol or price is None or qty is None or ts_ms is None:
            return

        price = float(price)
        qty = float(qty)
        timestamp = ts_ms / 1000.0
        symbol_upper = symbol.upper()

        for tf_name in TIMEFRAMES.keys():
            builder = candle_builders[symbol_upper][tf_name]
            completed = builder.process_trade(price, qty, timestamp)
            if completed:
                publish_candle_to_kafka(completed)

    except Exception as e:
        log.error(f"Error in on_message: {e}")


def on_error(ws, error):
    log.error(f"WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    log.warning(f"WebSocket closed: {close_status_code} {close_msg}")


def on_open(ws):
    log.info("✅ Binance WebSocket connected")

# --------------- MAIN ---------------
def main():
    log.info("Starting Binance streamer...")
    log.info(f"Symbols: {', '.join(symbols)}")
    log.info(f"Timeframes: {', '.join(TIMEFRAMES.keys())}")

    url = build_stream_url(stream_symbols)
    log.info(f"Connecting to: {url}")

    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # Keepalive pings help stay connected
    ws.run_forever(ping_interval=20, ping_timeout=10)


if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            log.info("Interrupted by user, exiting...")
            break
        except Exception as e:
            log.error(f"Streamer crashed, retrying in 5s: {e}")
            time.sleep(5)
