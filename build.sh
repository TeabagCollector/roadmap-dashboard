#!/bin/bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")" && pwd)"
app="$project_root/build/Roadmap Dashboard Preview.app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources/ui" "$app/Contents/Resources/runtime/sync" "$app/Contents/Resources/runtime/samples" "$project_root/build/module-cache"
python3 - "$project_root" "$app" <<'PY'
import sys,shutil,plistlib
from pathlib import Path
root,app=map(Path,sys.argv[1:])
for name in ('index.html','style.css','conversation-model.js','i18n.js','connection.js','app.js','demo-data.js','preview.js'):shutil.copyfile(root/'src'/name,app/'Contents/Resources/ui'/name)
for name in ('dashboard.py','setup.py','client.py'):shutil.copyfile(root/'sync'/name,app/'Contents/Resources/runtime/sync'/name)
shutil.copytree(root/'skills',app/'Contents/Resources/runtime/skills',dirs_exist_ok=True)
for cache in (app/'Contents/Resources/runtime').rglob('__pycache__'):shutil.rmtree(cache)
shutil.copyfile(root/'samples/demo.json',app/'Contents/Resources/runtime/samples/demo.json')
info={'CFBundleName':'Roadmap Dashboard Preview','CFBundleDisplayName':'Roadmap Dashboard Preview','CFBundleIdentifier':'local.roadmap-dashboard.preview','CFBundleExecutable':'roadmap-dashboard','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.4.0-preview','LSUIElement':True,'NSHighResolutionCapable':True,'LSMinimumSystemVersion':'15.0'}
(app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
PY
swiftc -module-cache-path "$project_root/build/module-cache" -framework AppKit -framework WebKit -framework Carbon "$project_root/src/Monitor.swift" -o "$app/Contents/MacOS/roadmap-dashboard"
codesign --force --sign - "$app" >/dev/null 2>&1
printf '%s\n' "$app"
