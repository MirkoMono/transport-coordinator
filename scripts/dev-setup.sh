#!/usr/bin/env bash
# One-time / repeat setup: Docker infra, Python venv, migrations.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Starting Postgres + Redis..."
make infra

if command -v python3.12 >/dev/null; then
  PYTHON=python3.12
else
  PYTHON=python3
fi

if [ ! -d ".venv" ]; then
  echo "==> Creating Python virtual environment..."
  $PYTHON -m venv .venv
fi

source .venv/bin/activate
echo "==> Installing Python packages..."
pip install -q -e "packages/solver[dev]" -e "packages/geospatial[dev]" -e "packages/ai[dev]" -e "apps/api[dev]"

echo "==> Running database migrations..."
make migrate

if [ ! -d "apps/web/node_modules" ]; then
  echo "==> Installing web dependencies..."
  cd apps/web && npm install && cd "$ROOT"
fi

echo ""
echo "Setup done. Now open TWO more terminal tabs and run:"
echo "  ./scripts/start-api.sh"
echo "  ./scripts/start-web.sh"
echo ""
echo "Then open http://localhost:5173"
