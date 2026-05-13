#!/usr/bin/env python3
"""Cursor hook: send agent metrics to cursor-metrics API on agent stop."""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

LOG_DIR = os.path.expanduser("~/.cursor/hooks-logs")
API_URL = os.environ.get("CURSOR_METRICS_URL", "http://localhost:8000")

COMMAND_SKILL_MAP = {
    "specify": "spec-creation",
    "design": "design-creation",
    "implement": "implementation",
    "review": "code-review",
}
MAX_TRANSCRIPT_LINES = 50


def _git_email() -> str:
    try:
        return subprocess.check_output(["git", "config", "user.email"], text=True, timeout=2).strip()
    except Exception:
        return os.environ.get("USER", "unknown") + "@local"


def _extract_user_text(event: dict) -> str | None:
    """Extract the actual user text from a transcript JSONL line.

    Handles two formats:
    - Simple: {"role": "user", "content": "text"}
    - Rich:   {"role": "user", "message": {"content": [{"type": "text", "text": "..."}]}}

    If the text contains <user_query> tags, extracts the content within.
    """
    content = event.get("content")
    if not content:
        msg = event.get("message", {})
        parts = msg.get("content", [])
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict) and part.get("type") == "text":
                    content = part.get("text", "")
                    break
        elif isinstance(parts, str):
            content = parts
    if not content:
        return None
    if "<user_query>" in content:
        try:
            start = content.index("<user_query>") + len("<user_query>")
            end = content.index("</user_query>", start)
            content = content[start:end]
        except ValueError:
            pass
    return content.strip()


def _find_command_in_text(text: str) -> str | None:
    """Find a /command anywhere in the text (handles prefixed commands like 'make /specify')."""
    import re

    match = re.search(r"(?:^|\s)/(\w[\w-]*)", text)
    return match.group(1) if match else None


def _extract_command(transcript_path: str | None) -> tuple[str | None, str | None]:
    """Read transcript JSONL, find first user message, extract /command."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return None, None
    try:
        with open(transcript_path) as f:
            for i, line in enumerate(f):
                if i >= MAX_TRANSCRIPT_LINES:
                    break
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("role") == "user":
                    text = _extract_user_text(event)
                    if not text:
                        return None, None
                    cmd = _find_command_in_text(text)
                    if cmd:
                        return cmd, COMMAND_SKILL_MAP.get(cmd)
                    return None, None
    except OSError:
        pass
    return None, None


def _extract_workspace(event: dict) -> str | None:
    roots = event.get("workspace_roots")
    if roots and isinstance(roots, list) and len(roots) > 0:
        return roots[0]
    return None


EVENT_TYPE_MAP = {
    "stop": "stop",
    "session_end": "session_end",
    "subagentStop": "subagent_stop",
}


def _build_payload(event: dict) -> dict:
    """Build the API ingest payload from a Cursor hook event."""
    hook_event_name = event.get("hook_event_name", "stop")
    user_email = event.get("user_email") or _git_email()

    command_name: str | None = None
    skill_name: str | None = None
    if hook_event_name == "stop":
        command_name, skill_name = _extract_command(event.get("transcript_path"))

    return {
        "event_type": EVENT_TYPE_MAP.get(hook_event_name, "stop"),
        "conversation_id": event.get("conversation_id", "unknown"),
        "generation_id": event.get("generation_id", "unknown"),
        "model": event.get("model", "unknown"),
        "user_email": user_email,
        "status": event.get("status", "completed"),
        "loop_count": event.get("loop_count"),
        "cursor_version": event.get("cursor_version"),
        "input_tokens": event.get("input_tokens"),
        "output_tokens": event.get("output_tokens"),
        "cache_read_tokens": event.get("cache_read_tokens"),
        "cache_write_tokens": event.get("cache_write_tokens"),
        "session_id": event.get("session_id"),
        "workspace": _extract_workspace(event),
        "command_name": command_name,
        "skill_name": skill_name,
        "subagent_type": event.get("subagent_type"),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    raw = sys.stdin.read()

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "stop-events.jsonl"), "a") as f:
        f.write(json.dumps({"ts": datetime.now(UTC).isoformat(), "raw": raw.strip()}) + "\n")

    event = json.loads(raw) if raw.strip() else {}
    payload = _build_payload(event)

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
