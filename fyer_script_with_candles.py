import os
import json
import logging
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from collections import defaultdict
from kafka import KafkaProducer

from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
from dotenv import load_dotenv

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

# ---------------- ENV ----------------
load_dotenv()
CLIENT_ID = os.getenv("FYERS_APP_ID")
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI")

symbols = [
    "NSE:RELIANCE-EQ","NSE:TCS-EQ","NSE:INFY-EQ","NSE:HDFCBANK-EQ",
    "NSE:ICICIBANK-EQ","NSE:SBIN-EQ","NSE:LT-EQ","NSE:ITC-EQ",
    "NSE:HINDUNILVR-EQ","NSE:AXISBANK-EQ"
]

# Timeframes in seconds
TIMEFRAMES = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "1d": 86400
}

AUTH_CODE = None

# ---------------- KAFKA PRODUCER ----------------
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None
)

# ---------------- CANDLE BUILDER ----------------
class CandleBuilder:
    def __init__(self, symbol, timeframe_seconds, timeframe_name):
        self.symbol = symbol
        self.timeframe_seconds = timeframe_seconds
        self.timeframe_name = timeframe_name
        self.current_candle = None
        self.candle_start_time = None
        
    def get_candle_start_time(self, timestamp):
        """Get the start time of the candle for the given timestamp"""
        dt = datetime.fromtimestamp(timestamp)
        
        if self.timeframe_seconds == 86400:  # 1 day
            return datetime(dt.year, dt.month, dt.day).timestamp()
        elif self.timeframe_seconds == 3600:  # 1 hour
            return datetime(dt.year, dt.month, dt.day, dt.hour).timestamp()
        else:  # Minutes
            minutes = self.timeframe_seconds // 60
            minute_slot = (dt.minute // minutes) * minutes
            return datetime(dt.year, dt.month, dt.day, dt.hour, minute_slot).timestamp()
    
    def process_tick(self, tick_data):
        """Process incoming tick data and build candles"""
        try:
            timestamp = tick_data.get('last_traded_time')
            if not timestamp:
                return None
            
            ltp = tick_data.get('ltp')
            volume = tick_data.get('vol_traded_today', 0)
            
            if not ltp:
                return None
            
            candle_start = self.get_candle_start_time(timestamp)
            
            # Check if we need to create a new candle
            if self.current_candle is None or candle_start != self.candle_start_time:
                # Save the previous candle if it exists
                completed_candle = None
                if self.current_candle is not None:
                    completed_candle = self.current_candle.copy()
                    completed_candle['closed'] = True
                
                # Start a new candle
                self.candle_start_time = candle_start
                self.current_candle = {
                    'symbol': self.symbol,
                    'timeframe': self.timeframe_name,
                    'timestamp': int(candle_start),
                    'datetime': datetime.fromtimestamp(candle_start).isoformat(),
                    'open': ltp,
                    'high': ltp,
                    'low': ltp,
                    'close': ltp,
                    'volume': volume,
                    'closed': False
                }
                
                return completed_candle
            else:
                # Update current candle
                self.current_candle['high'] = max(self.current_candle['high'], ltp)
                self.current_candle['low'] = min(self.current_candle['low'], ltp)
                self.current_candle['close'] = ltp
                self.current_candle['volume'] = volume
                
                return None
                
        except Exception as e:
            log.error(f"Error processing tick for {self.symbol} {self.timeframe_name}: {e}")
            return None

# Store candle builders for each symbol and timeframe
candle_builders = defaultdict(dict)

# Initialize candle builders for all symbols and timeframes
for symbol in symbols:
    for tf_name, tf_seconds in TIMEFRAMES.items():
        candle_builders[symbol][tf_name] = CandleBuilder(symbol, tf_seconds, tf_name)

# ---------------- AUTH SERVER ----------------
class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global AUTH_CODE
        qs = parse_qs(urlparse(self.path).query)
        AUTH_CODE = qs.get("auth_code", [None])[0]

        log.info(f"Redirect params: {qs}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Auth successful. Close this tab.")
    
    def log_message(self, format, *args):
        pass  # Suppress default HTTP server logs

def get_auth_code(session):
    auth_url = session.generate_authcode()
    log.info(f"Opening login URL: {auth_url}")
    webbrowser.open(auth_url)

    HTTPServer(("127.0.0.1", 8080), AuthHandler).handle_request()
    return AUTH_CODE

# ---------------- KAFKA PUBLISH ----------------
def publish_candle_to_kafka(candle):
    """Publish completed candle to Kafka"""
    try:
        symbol = candle['symbol'].replace(':', '_').replace('-', '_')
        timeframe = candle['timeframe']
        topic = f"candles_{symbol}_{timeframe}"
        
        producer.send(
            topic,
            key=candle['symbol'],
            value=candle
        )
        
        log.info(f"📊 Candle published to {topic}: O={candle['open']:.2f} H={candle['high']:.2f} L={candle['low']:.2f} C={candle['close']:.2f} V={candle['volume']}")
        
    except Exception as e:
        log.error(f"Error publishing candle to Kafka: {e}")

# ---------------- AUTH FLOW ----------------
log.info("Starting Fyers authentication...")
session = fyersModel.SessionModel(
    client_id=CLIENT_ID,
    secret_key=SECRET_KEY,
    redirect_uri=REDIRECT_URI,
    response_type="code",
    grant_type="authorization_code"
)

auth_code = get_auth_code(session)
if not auth_code:
    raise RuntimeError("Auth code not received")

log.info("Auth code received")

session.set_token(auth_code)

log.info("Calling generate_token()")
token_response = session.generate_token()

# ✅ SAFE TOKEN EXTRACTION
ACCESS_TOKEN = (
    token_response.get("access_token")
    or token_response.get("data", {}).get("access_token")
)

if not ACCESS_TOKEN:
    raise RuntimeError("Access token NOT found in response")

log.info("Access token extracted successfully")

# ---------------- WEBSOCKET ----------------
def on_connect():
    log.info("✅ WebSocket connected")
    ws.subscribe(symbols=symbols, data_type="SymbolUpdate")
    ws.keep_running()

def on_message(msg):
    """Process incoming tick data and build candles"""
    try:
        symbol = msg.get('symbol')
        if not symbol:
            return
        
        # Process tick for all timeframes
        for tf_name in TIMEFRAMES.keys():
            builder = candle_builders[symbol][tf_name]
            completed_candle = builder.process_tick(msg)
            
            # If a candle was completed, publish it to Kafka
            if completed_candle:
                publish_candle_to_kafka(completed_candle)
                
    except Exception as e:
        log.error(f"Error in on_message: {e}")

def on_error(err):
    log.error(f"❌ WebSocket error: {err}")

def on_close():
    log.warning("⚠️  WebSocket closed")

ws = data_ws.FyersDataSocket(
    access_token=f"{CLIENT_ID}:{ACCESS_TOKEN}",
    on_connect=on_connect,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

log.info("Starting WebSocket connection...")
log.info(f"Tracking {len(symbols)} symbols across {len(TIMEFRAMES)} timeframes")
log.info(f"Timeframes: {', '.join(TIMEFRAMES.keys())}")

try:
    ws.connect()
except KeyboardInterrupt:
    log.info("Shutting down...")
    producer.flush()
    producer.close()
except Exception as e:
    log.error(f"Error: {e}")
    producer.close()
