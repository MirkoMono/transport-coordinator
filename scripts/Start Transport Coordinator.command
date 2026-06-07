#!/bin/bash
# Resolve symlink when launched from Desktop
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd "$(dirname "$SOURCE")" && pwd)"
cd "$(cd "$SCRIPT_DIR/.." && pwd)"

./scripts/start.sh

echo ""
read -r -p "Press Enter to close this window (app keeps running)…"
