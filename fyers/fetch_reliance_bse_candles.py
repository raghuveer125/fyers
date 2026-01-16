import os
import logging
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values
# Using psycopg2-binary which doesn't require compilation
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger(__name__)

load_dotenv()
CLIENT_ID = os.getenv("FYERS_APP_ID")
SECRET_KEY = os.getenv("FYERS_SECRET_KEY")
REDIRECT_URI = os.getenv("FYERS_REDIRECT_URI")

SYMBOL = "BSE:RELIANCE-A"

TIMEFRAMES = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "1D": "D"
}

AUTH_CODE = None


class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global AUTH_CODE
        qs = parse_qs(urlparse(self.path).query)
        AUTH_CODE = qs.get("auth_code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Auth successful. Close this tab.")

    def log_message(self, format, *args):
        pass


def get_auth_code(session):
    auth_url = session.generate_authcode()
    log.info(f"Opening login URL: {auth_url}")
    webbrowser.open(auth_url)
    HTTPServer(("127.0.0.1", 8080), AuthHandler).handle_request()
    return AUTH_CODE


def create_database():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="trader",
        password="trader123",
        dbname="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'fyers'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE fyers")
        log.info("Database 'fyers' created")
    else:
        log.info("Database 'fyers' already exists")
    cur.close()
    conn.close()


def create_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS candles (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(50) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            timestamp BIGINT NOT NULL,
            datetime TIMESTAMP NOT NULL,
            open DOUBLE PRECISION NOT NULL,
            high DOUBLE PRECISION NOT NULL,
            low DOUBLE PRECISION NOT NULL,
            close DOUBLE PRECISION NOT NULL,
            volume BIGINT NOT NULL,
            UNIQUE(symbol, timeframe, timestamp)
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_candles_symbol_timeframe
        ON candles(symbol, timeframe)
    """)
    conn.commit()
    cur.close()
    log.info("Table 'candles' ready")


def fetch_candles(fyers, symbol, timeframe_name, resolution):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    data = {
        "symbol": symbol,
        "resolution": resolution,
        "date_format": "1",
        "range_from": start_date.strftime("%Y-%m-%d"),
        "range_to": end_date.strftime("%Y-%m-%d"),
        "cont_flag": "1"
    }

    response = fyers.history(data=data)

    if response.get("s") != "ok":
        log.error(f"Failed to fetch {timeframe_name}: {response}")
        return []

    candles = response.get("candles", [])
    log.info(f"Fetched {len(candles)} candles for {timeframe_name}")
    return candles


def save_candles(conn, symbol, timeframe_name, candles):
    if not candles:
        return

    cur = conn.cursor()
    seen = set()
    rows = []
    for c in candles:
        ts = c[0]
        if ts in seen:
            continue
        seen.add(ts)
        dt = datetime.fromtimestamp(ts)
        rows.append((
            symbol,
            timeframe_name,
            ts,
            dt,
            c[1],  # open
            c[2],  # high
            c[3],  # low
            c[4],  # close
            c[5]   # volume
        ))

    execute_values(
        cur,
        """
        INSERT INTO candles (symbol, timeframe, timestamp, datetime, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """,
        rows
    )
    conn.commit()
    cur.close()
    log.info(f"Saved {len(rows)} candles for {timeframe_name}")


def main():
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
    token_response = session.generate_token()

    access_token = (
        token_response.get("access_token")
        or token_response.get("data", {}).get("access_token")
    )

    if not access_token:
        raise RuntimeError("Access token NOT found in response")

    log.info("Access token extracted successfully")

    fyers = fyersModel.FyersModel(
        client_id=CLIENT_ID,
        is_async=False,
        token=access_token,
        log_path=""
    )

    create_database()

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="trader",
        password="trader123",
        dbname="fyers"
    )

    create_table(conn)

    for tf_name, resolution in TIMEFRAMES.items():
        log.info(f"Fetching {tf_name} candles for {SYMBOL}...")
        candles = fetch_candles(fyers, SYMBOL, tf_name, resolution)
        save_candles(conn, SYMBOL, tf_name, candles)

    conn.close()
    log.info("Done!")


if __name__ == "__main__":
    main()
