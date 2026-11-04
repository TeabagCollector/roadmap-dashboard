#!/bin/bash
set -euo pipefail
package_root="$(cd "$(dirname "$0")" && pwd)"
python3 "$package_root/scripts/install.py"
open "$HOME/Applications/Roadmap Dashboard Preview.app"
