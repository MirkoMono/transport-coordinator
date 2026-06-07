#!/usr/bin/env bash
# Place Start/Stop shortcuts on macOS Desktop (symlinks into this repo).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP="${HOME}/Desktop"

if [ ! -d "$DESKTOP" ]; then
  echo "Desktop folder not found: $DESKTOP"
  exit 1
fi

chmod +x "$ROOT/scripts/start.sh" "$ROOT/scripts/stop.sh"
chmod +x "$ROOT/scripts/Start Transport Coordinator.command"
chmod +x "$ROOT/scripts/Stop Transport Coordinator.command"

ln -sf "$ROOT/scripts/Start Transport Coordinator.command" \
  "$DESKTOP/Start Transport Coordinator.command"
ln -sf "$ROOT/scripts/Stop Transport Coordinator.command" \
  "$DESKTOP/Stop Transport Coordinator.command"

echo "Desktop shortcuts created:"
echo "  $DESKTOP/Start Transport Coordinator.command"
echo "  $DESKTOP/Stop Transport Coordinator.command"
echo ""
echo "Double-click Start to launch the app. Double-click Stop when finished."
