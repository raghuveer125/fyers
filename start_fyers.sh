#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/fyers_streamer.pid"
LOG_FILE="$ROOT_DIR/fyers_streamer.log"
SCRIPT="$ROOT_DIR/fyers/fyer_script_with_candles.py"
SYMBOLS_FILE="$ROOT_DIR/fyers/symbols.json"

if [[ ! -f "$SCRIPT" ]]; then
  echo "Fyers streamer script not found: $SCRIPT" >&2
  exit 1
fi
if [[ ! -f "$SYMBOLS_FILE" ]]; then
  echo "Symbols file missing: $SYMBOLS_FILE" >&2
  exit 1
fi

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE")"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Fyers streamer already running with PID $old_pid" >&2
    exit 1
  else
    echo "Removing stale PID file"
    rm -f "$PID_FILE"
  fi
fi

set -a
if [[ -f "$ROOT_DIR/.env" ]]; then
  . "$ROOT_DIR/.env"
fi
set +a

PYTHON_BIN="python3"
if [[ -x "$ROOT_DIR/venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/venv/bin/python"
fi

nohup "$PYTHON_BIN" -u "$SCRIPT" >> "$LOG_FILE" 2>&1 &
new_pid=$!
echo "$new_pid" > "$PID_FILE"
echo "Started Fyers streamer (PID $new_pid). Logs: $LOG_FILE"
