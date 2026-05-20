#!/usr/bin/env bash
#
# Install the Cursor Reporting hook for the current user.
#
# Usage:
#   ./scripts/install-hook.sh                          # defaults to localhost:8000
#   CURSOR_METRICS_URL=https://metrics.example.com ./scripts/install-hook.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CURSOR_DIR="$HOME/.cursor"
HOOKS_DIR="$CURSOR_DIR/hooks"
HOOKS_JSON="$CURSOR_DIR/hooks.json"

echo "==> Installing Cursor Reporting hook..."

mkdir -p "$HOOKS_DIR" "$CURSOR_DIR/hooks-logs"

cp "$REPO_DIR/scripts/send-metrics.py" "$HOOKS_DIR/send-metrics.py"
chmod +x "$HOOKS_DIR/send-metrics.py"
echo "    Copied send-metrics.py -> $HOOKS_DIR/send-metrics.py"

if [ -f "$HOOKS_JSON" ]; then
    if grep -q "send-metrics.py" "$HOOKS_JSON"; then
        echo "    hooks.json already contains send-metrics.py — skipping."
    else
        echo "    WARNING: $HOOKS_JSON already exists but does not reference send-metrics.py."
        echo "    Please manually add the stop hook entry. See README for details."
    fi
else
    cat > "$HOOKS_JSON" <<'HOOKEOF'
{
  "version": 1,
  "hooks": {
    "stop": [
      {
        "command": "hooks/send-metrics.py",
        "timeout": 10,
        "loop_limit": null
      }
    ],
    "subagentStop": [
      {
        "command": "hooks/send-metrics.py",
        "timeout": 10,
        "loop_limit": null
      }
    ]
  }
}
HOOKEOF
    echo "    Created $HOOKS_JSON"
fi

API_URL="${CURSOR_METRICS_URL:-http://localhost:8000}"
echo ""
echo "==> Done! The hook will POST to: $API_URL/api/v1/ingest"
echo "    To change the API URL, set CURSOR_METRICS_URL in your shell environment."
echo "    Debug logs: ~/.cursor/hooks-logs/stop-events.jsonl"
echo ""
echo "    Restart Cursor to activate the hook."
