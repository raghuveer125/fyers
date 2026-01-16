import os
import json
import logging
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

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

AUTH_CODE = None

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

def get_auth_code(session):
    auth_url = session.generate_authcode()
    log.info(f"Opening login URL: {auth_url}")
    webbrowser.open(auth_url)

    HTTPServer(("127.0.0.1", 8080), AuthHandler).handle_request()
    return AUTH_CODE

# ---------------- AUTH FLOW ----------------
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

log.info(f"Raw token response: {json.dumps(token_response, indent=2)}")

# ✅ SAFE TOKEN EXTRACTION (works across SDK versions)
ACCESS_TOKEN = (
    token_response.get("access_token")
    or token_response.get("data", {}).get("access_token")
)

if not ACCESS_TOKEN:
    raise RuntimeError("Access token NOT found in response")

log.info("Access token extracted successfully")

# ---------------- WEBSOCKET ----------------
def on_connect():
    log.info("WebSocket connected")
    ws.subscribe(symbols=symbols, data_type="SymbolUpdate")
    ws.keep_running()

def on_message(msg):
    log.info(f"TICK: {msg}")

def on_error(err):
    log.error(err)

def on_close():
    log.warning("WebSocket closed")

ws = data_ws.FyersDataSocket(
    access_token=f"{CLIENT_ID}:{ACCESS_TOKEN}",
    on_connect=on_connect,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.connect()
