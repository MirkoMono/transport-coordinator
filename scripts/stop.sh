#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$ROOT/.run"

stop_pid() {
  local name=$1
  local pid_file="$RUN_DIR/${name}.pid"
  if [ ! -f "$pid_file" ]; then
    return 0
  fi
  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    pkill -P "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file"
}

stop_pid api
stop_pid web

# Fallback if processes were started outside start.sh
if command -v lsof >/dev/null 2>&1; then
  lsof -ti:8000 2>/dev/null | xargs kill 2>/dev/null || true
  lsof -ti:5173 2>/dev/null | xargs kill 2>/dev/null || true
fi

echo "Transport Coordinator stopped."
