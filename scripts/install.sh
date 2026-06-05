#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Transport Coordinator — on-premise install"

if ! command -v docker >/dev/null; then
  echo "Docker is required. Install Docker Desktop and retry."
  exit 1
fi

echo "==> Starting Postgres, Redis, and API..."
docker compose -f docker/compose.yml up -d --build

echo "==> Waiting for database..."
sleep 8

if command -v python3.12 >/dev/null; then
  PYTHON=python3.12
elif command -v python3 >/dev/null; then
  PYTHON=python3
else
  echo "Python 3.12+ required for migrations."
  exit 1
fi

if [ ! -d ".venv" ]; then
  $PYTHON -m venv .venv
fi
source .venv/bin/activate
pip install -q -e "packages/solver" -e "packages/geospatial" -e "apps/api"
cd apps/api && alembic upgrade head && cd "$ROOT"

echo ""
echo "Install complete."
echo "  API:      http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Start the web UI:"
echo "  cd apps/web && npm install && npm run dev"
echo "  Open http://localhost:5173 (coordinator) or http://localhost:5173/driver"
