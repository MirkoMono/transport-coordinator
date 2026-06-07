#!/usr/bin/env bash
# Start API + web UI in the background and open the coordinator in your browser.
# Usage:
#   ./scripts/start.sh           # localhost only
#   ./scripts/start.sh --mobile  # same Wi‑Fi — test on phone (see docs/demo-manual-sv.md)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
RUN_DIR="$ROOT/.run"
mkdir -p "$RUN_DIR"

MOBILE=0
if [[ "${1:-}" == "--mobile" ]]; then
  MOBILE=1
fi

if [ ! -d ".venv" ]; then
  echo "==> First-time setup (no Docker)..."
  ./scripts/dev-no-docker.sh
fi

start_api() {
  if [ -f "$RUN_DIR/api.pid" ] && kill -0 "$(cat "$RUN_DIR/api.pid")" 2>/dev/null; then
    echo "API already running (pid $(cat "$RUN_DIR/api.pid"))."
    return 0
  fi
  source .venv/bin/activate
  nohup uvicorn transport_api.main:app --reload --host 127.0.0.1 --port 8000 \
    >"$RUN_DIR/api.log" 2>&1 &
  echo $! >"$RUN_DIR/api.pid"
  echo "API starting..."
}

start_web() {
  if [ -f "$RUN_DIR/web.pid" ] && kill -0 "$(cat "$RUN_DIR/web.pid")" 2>/dev/null; then
    echo "Web UI already running (pid $(cat "$RUN_DIR/web.pid"))."
    return 0
  fi
  cd "$ROOT/apps/web"
  if [ "$MOBILE" -eq 1 ]; then
    TRANSPORT_MOBILE=1 nohup npm run dev >"$RUN_DIR/web.log" 2>&1 &
  else
    nohup npm run dev >"$RUN_DIR/web.log" 2>&1 &
  fi
  echo $! >"$RUN_DIR/web.pid"
  cd "$ROOT"
  echo "Web UI starting..."
}

wait_for() {
  local url=$1
  local label=$2
  for _ in $(seq 1 45); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "$label ready."
      return 0
    fi
    sleep 1
  done
  echo "WARNING: $label did not respond in time. Check .run/*.log"
  return 1
}

start_api
wait_for "http://localhost:8000/health" "API" || true
start_web
wait_for "http://localhost:5173" "Web UI" || true

COORD_URL="http://localhost:5173"
if command -v open >/dev/null 2>&1; then
  open "$COORD_URL" 2>/dev/null || true
fi

echo ""
echo "Transport Coordinator is running."
echo "  Coordinator: $COORD_URL"
echo "  Driver:      $COORD_URL/driver"
echo "  API health:  http://localhost:8000/health"
echo ""

if [ "$MOBILE" -eq 1 ]; then
  LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
  if [ -n "$LAN_IP" ]; then
    echo "Mobile (same Wi‑Fi):"
    echo "  Coordinator: http://${LAN_IP}:5173"
    echo "  Driver:      http://${LAN_IP}:5173/driver"
  else
    echo "Mobile: could not detect LAN IP. Try: ipconfig getifaddr en0"
  fi
  echo ""
fi

echo "Logs:  .run/api.log  .run/web.log"
echo "Stop:  ./scripts/stop.sh"
echo "Help:  docs/demo-manual-sv.md"
