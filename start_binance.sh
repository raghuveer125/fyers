#!/usr/bin/env bash
set -euo pipefail

# Paths
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/binance_streamer.pid"
LOG_FILE="$ROOT_DIR/binance_streamer.log"
SCRIPT="$ROOT_DIR/binance/binance_candles.py"
SYMBOLS_FILE="$ROOT_DIR/binance/symbols_crypto.json"

# Require script and symbols
if [[ ! -f "$SCRIPT" ]]; then
  echo "Binance streamer script not found: $SCRIPT" >&2
  exit 1
fi
if [[ ! -f "$SYMBOLS_FILE" ]]; then
  echo "Symbols file missing: $SYMBOLS_FILE" >&2
  exit 1
fi

# Handle existing PID
if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE")"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Streamer already running with PID $old_pid" >&2
    exit 1
  else
    echo "Removing stale PID file"
    rm -f "$PID_FILE"
  fi
fi

# Load environment from .env if present
set -a
if [[ -f "$ROOT_DIR/.env" ]]; then
  . "$ROOT_DIR/.env"
fi
set +a

# Choose python (prefer venv)
PYTHON_BIN="python3"
if [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
fi

# Start background process
nohup "$PYTHON_BIN" -u "$SCRIPT" >> "$LOG_FILE" 2>&1 &
new_pid=$!
echo "$new_pid" > "$PID_FILE"
echo "Started binance streamer (PID $new_pid). Logs: $LOG_FILE"
