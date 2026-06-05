#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ ! -d ".venv" ]; then
  echo "Run setup first: make setup-local"
  exit 1
fi
source .venv/bin/activate
echo "API starting at http://localhost:8000"
echo "Leave this terminal running. Open http://localhost:8000/docs to verify."
make api
