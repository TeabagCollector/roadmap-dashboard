#!/bin/bash
set -euo pipefail
preview_root="$(cd "$(dirname "$0")" && pwd)"
app="$preview_root/build/Roadmap Dashboard Preview.app/Contents/MacOS/roadmap-dashboard"
if [ ! -x "$app" ]; then bash "$preview_root/build.sh"; fi
exec "$app" --language zh
