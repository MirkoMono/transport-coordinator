#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/web"

echo "Waiting for API at http://localhost:8000 ..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "API is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo ""
    echo "WARNING: API not responding on port 8000."
    echo "Start it first in another terminal:"
    echo "  ./scripts/start-api.sh"
    echo ""
  fi
  sleep 1
done

echo "Web UI starting at http://localhost:5173"
npm run dev
