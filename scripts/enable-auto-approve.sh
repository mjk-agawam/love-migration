#!/usr/bin/env bash
# Run this once from your terminal to enable auto-approve globally for Claude Code.
# Cursor: go to Settings > Features > Agent and enable "Auto-run" (Yolo mode).
set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"

if [[ ! -f "$SETTINGS" ]]; then
  echo '{"dangerouslySkipPermissions": true}' > "$SETTINGS"
  echo "Created $SETTINGS with dangerouslySkipPermissions: true"
  exit 0
fi

python3 - <<'PYEOF'
import json, os, sys

path = os.path.expanduser("~/.claude/settings.json")
with open(path) as f:
    s = json.load(f)

if s.get("dangerouslySkipPermissions"):
    print("Already set — dangerouslySkipPermissions is true in", path)
    sys.exit(0)

s["dangerouslySkipPermissions"] = True

with open(path, "w") as f:
    json.dump(s, f, indent=2)
    f.write("\n")

print("Done. dangerouslySkipPermissions = true written to", path)
print("Restart Claude Code for the change to take effect.")
PYEOF
