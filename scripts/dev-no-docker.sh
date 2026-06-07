#!/usr/bin/env bash
# Local dev WITHOUT Docker — API + web UI, no Postgres/Redis.
# Good for testing optimize + map UI. Run history/diff need Docker later.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v python3.12 >/dev/null; then
  PYTHON=python3.12
elif command -v python3 >/dev/null; then
  PYTHON=python3
else
  echo "Python 3.12+ required. Install: brew install python@3.12"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment..."
  $PYTHON -m venv .venv
fi

source .venv/bin/activate
echo "==> Installing Python packages..."
pip install -q -e "packages/solver[dev]" -e "packages/geospatial[dev]" -e "packages/ai[dev]" -e "apps/api[dev]"

if [ ! -d "apps/web/node_modules" ]; then
  echo "==> Installing web packages..."
  (cd apps/web && npm install)
fi

echo ""
echo "Setup complete (no Docker)."
echo ""
echo "Easiest — one command (opens browser):"
echo ""
echo "  ./scripts/start.sh"
echo ""
echo "Or desktop shortcut:"
echo ""
echo "  ./scripts/install-desktop-shortcut.sh"
echo ""
echo "Advanced — two terminals:"
echo ""
echo "  ./scripts/start-api.sh"
echo "  ./scripts/start-web.sh"
