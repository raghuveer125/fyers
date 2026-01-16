# fyers_full_flow.py
import os, json, webbrowser, requests, websocket
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

APP_ID    = os.getenv("FYERS_APP_ID")
SECRET_ID = os.getenv("FYERS_SECRET_ID")
REDIRECT  = os.getenv("FYERS_REDIRECT_URI")  # e.g. http://127.0.0.1:8080/
WS_URL    = "wss://socket.fyers.in/data"

symbols = [
    "NSE:RELIANCE-EQ","NSE:TCS-EQ","NSE:INFY-EQ","NSE:HDFCBANK-EQ",
    "NSE:ICICIBANK-EQ","NSE:SBIN-EQ","NSE:LT-EQ","NSE:ITC-EQ",
    "NSE:HINDUNILVR-EQ","NSE:AXISBANK-EQ"
]

AUTH_CODE = None

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global AUTH_CODE
        qs = parse_qs(urlparse(self.path).query)
        AUTH_CODE = qs.get("auth_code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Auth code received. You can close this tab.")

def get_auth_code():
    url = (
        "https://api.fyers.in/api/v2/generate-authcode"
        f"?client_id={APP_ID}&redirect_uri={REDIRECT}&response_type=code"
    )
    webbrowser.open(url)
    HTTPServer(("127.0.0.1", 8080), AuthHandler).handle_request()
    return AUTH_CODE

def get_access_token(code):
    r = requests.post(
        "https://api.fyers.in/api/v2/token",
        json={
            "grant_type":"authorization_code",
            "appIdHash":f"{APP_ID}:{SECRET_ID}",
            "code":code,
            "redirect_uri":REDIRECT
        }
    )
    return r.json()["access_token"]

def on_open(ws):
    ws.send(json.dumps({"T":"auth","app_id":APP_ID,"token":ACCESS_TOKEN}))
    ws.send(json.dumps({"T":"subscribe","L":symbols}))
    print("✅ Subscribed")

def on_message(ws, msg): print(msg)

if __name__ == "__main__":
    code = get_auth_code()
    ACCESS_TOKEN = get_access_token(code)
    websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message
    ).run_forever()
