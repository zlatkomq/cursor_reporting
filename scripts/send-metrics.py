#!/usr/bin/env python3
"""Cursor hook: send agent metrics to cursor-metrics API on agent stop."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

LOG_DIR = os.path.expanduser("~/.cursor/hooks-logs")
API_URL = os.environ.get("CURSOR_METRICS_URL", "http://localhost:8000")


def _git_email() -> str:
    try:
        return subprocess.check_output(
            ["git", "config", "user.email"], text=True, timeout=2
        ).strip()
    except Exception:
        return os.environ.get("USER", "unknown") + "@local"


def main() -> None:
    raw = sys.stdin.read()

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "stop-events.jsonl"), "a") as f:
        f.write(
            json.dumps(
                {"ts": datetime.now(timezone.utc).isoformat(), "raw": raw.strip()}
            )
            + "\n"
        )

    event = json.loads(raw) if raw.strip() else {}

    payload = {
        "event_type": "stop",
        "conversation_id": event.get("conversationId", event.get("id", "unknown")),
        "generation_id": event.get("generationId", "unknown"),
        "model": event.get("model", event.get("modelName", "unknown")),
        "user_email": _git_email(),
        "status": event.get("status", "completed"),
        "duration_ms": event.get("durationMs"),
        "loop_count": event.get("loopCount"),
        "cursor_version": event.get("cursorVersion"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        req = Request(
            f"{API_URL}/api/v1/ingest",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        urlopen(req, timeout=5)
    except (URLError, OSError):
        pass

    print("{}")


if __name__ == "__main__":
    main()
