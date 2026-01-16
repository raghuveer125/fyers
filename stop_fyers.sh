#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/fyers_streamer.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No PID file found ($PID_FILE). Nothing to stop."
  exit 0
fi

pid="$(cat "$PID_FILE")"
if [[ -z "$pid" ]]; then
  echo "PID file is empty. Removing it." >&2
  rm -f "$PID_FILE"
  exit 1
fi

if ! kill -0 "$pid" 2>/dev/null; then
  echo "Process $pid not running. Removing stale PID file."
  rm -f "$PID_FILE"
  exit 0
fi

kill "$pid" 2>/dev/null || true
for i in {1..10}; do
  if kill -0 "$pid" 2>/dev/null; then
    sleep 0.5
  else
    break
  fi
done

if kill -0 "$pid" 2>/dev/null; then
  echo "Force killing $pid"
  kill -9 "$pid" 2>/dev/null || true
fi

rm -f "$PID_FILE"
echo "Stopped Fyers streamer (PID $pid)."
