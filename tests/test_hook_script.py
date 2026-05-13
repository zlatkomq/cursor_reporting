"""Standalone tests for the send-metrics.py hook script (no FastAPI required)."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "send_metrics", Path(__file__).parent.parent / "scripts" / "send-metrics.py"
)
send_metrics = importlib.util.module_from_spec(spec)
sys.modules["send_metrics"] = send_metrics
spec.loader.exec_module(send_metrics)

SAMPLE_CURSOR_EVENT = {
    "conversation_id": "abc-123",
    "generation_id": "gen-456",
    "model": "claude-opus-4-6",
    "status": "completed",
    "loop_count": 3,
    "input_tokens": 2117969,
    "output_tokens": 19841,
    "cache_read_tokens": 2046472,
    "cache_write_tokens": 71458,
    "session_id": "sess-789",
    "hook_event_name": "stop",
    "cursor_version": "3.3.30",
    "workspace_roots": ["/home/k/Desktop/AI/cursor-metrics"],
    "user_email": "dev@company.com",
    "transcript_path": "/path/to/transcript.jsonl",
}


# -- _extract_workspace tests -------------------------------------------------


class TestExtractWorkspace:
    def test_valid_list(self):
        event = {"workspace_roots": ["/home/k/project-a", "/home/k/project-b"]}
        assert send_metrics._extract_workspace(event) == "/home/k/project-a"

    def test_empty_list(self):
        assert send_metrics._extract_workspace({"workspace_roots": []}) is None

    def test_missing_key(self):
        assert send_metrics._extract_workspace({}) is None

    def test_non_list_value(self):
        assert send_metrics._extract_workspace({"workspace_roots": "/a/path"}) is None

    def test_single_root(self):
        event = {"workspace_roots": ["/only/one"]}
        assert send_metrics._extract_workspace(event) == "/only/one"


# -- _git_email smoke test ----------------------------------------------------


class TestGitEmail:
    def test_returns_string(self):
        result = send_metrics._git_email()
        assert isinstance(result, str)
        assert len(result) > 0


# -- _build_payload tests -----------------------------------------------------


class TestBuildPayload:
    def test_full_cursor_event(self):
        payload = send_metrics._build_payload(SAMPLE_CURSOR_EVENT)

        assert payload["event_type"] == "stop"
        assert payload["conversation_id"] == "abc-123"
        assert payload["generation_id"] == "gen-456"
        assert payload["model"] == "claude-opus-4-6"
        assert payload["user_email"] == "dev@company.com"
        assert payload["status"] == "completed"
        assert payload["loop_count"] == 3
        assert payload["cursor_version"] == "3.3.30"
        assert payload["input_tokens"] == 2117969
        assert payload["output_tokens"] == 19841
        assert payload["cache_read_tokens"] == 2046472
        assert payload["cache_write_tokens"] == 71458
        assert payload["session_id"] == "sess-789"
        assert payload["workspace"] == "/home/k/Desktop/AI/cursor-metrics"
        assert "timestamp" in payload

    def test_transcript_populates_command_and_skill(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(json.dumps({"role": "user", "content": "/specify 003 expand"}) + "\n")
        event = {**SAMPLE_CURSOR_EVENT, "transcript_path": str(transcript)}
        payload = send_metrics._build_payload(event)
        assert payload["command_name"] == "specify"
        assert payload["skill_name"] == "spec-creation"

    def test_empty_event_defaults(self):
        payload = send_metrics._build_payload({})

        assert payload["event_type"] == "stop"
        assert payload["conversation_id"] == "unknown"
        assert payload["generation_id"] == "unknown"
        assert payload["model"] == "unknown"
        assert payload["status"] == "completed"
        assert payload["loop_count"] is None
        assert payload["cursor_version"] is None
        assert payload["input_tokens"] is None
        assert payload["output_tokens"] is None
        assert payload["cache_read_tokens"] is None
        assert payload["cache_write_tokens"] is None
        assert payload["session_id"] is None
        assert payload["workspace"] is None

    def test_no_duration_ms_in_payload(self):
        """duration_ms should NOT be in the payload — Cursor doesn't provide it."""
        payload = send_metrics._build_payload(SAMPLE_CURSOR_EVENT)
        assert "duration_ms" not in payload

    def test_user_email_falls_back_to_git(self):
        """When user_email is missing from event, fall back to _git_email()."""
        event = {**SAMPLE_CURSOR_EVENT}
        del event["user_email"]
        with patch.object(send_metrics, "_git_email", return_value="git@fallback.com"):
            payload = send_metrics._build_payload(event)
        assert payload["user_email"] == "git@fallback.com"

    def test_user_email_empty_string_falls_back(self):
        """Empty string user_email should trigger git fallback."""
        event = {**SAMPLE_CURSOR_EVENT, "user_email": ""}
        with patch.object(send_metrics, "_git_email", return_value="git@fallback.com"):
            payload = send_metrics._build_payload(event)
        assert payload["user_email"] == "git@fallback.com"

    def test_hook_event_name_maps_to_event_type(self):
        event = {**SAMPLE_CURSOR_EVENT, "hook_event_name": "session_end"}
        payload = send_metrics._build_payload(event)
        assert payload["event_type"] == "session_end"


# -- _extract_command tests ----------------------------------------------------


class TestExtractCommand:
    def test_specify_command(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(json.dumps({"role": "user", "content": "/specify 003 expand telemetry"}) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd == "specify"
        assert skill == "spec-creation"

    def test_design_command(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(json.dumps({"role": "user", "content": "/design 003"}) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd == "design"
        assert skill == "design-creation"

    def test_unknown_command(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(json.dumps({"role": "user", "content": "/unknown-cmd foo"}) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd == "unknown-cmd"
        assert skill is None

    def test_normal_message_no_command(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(json.dumps({"role": "user", "content": "just a normal message"}) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd is None
        assert skill is None

    def test_missing_file(self):
        cmd, skill = send_metrics._extract_command("/nonexistent/path.jsonl")
        assert cmd is None
        assert skill is None

    def test_none_path(self):
        cmd, skill = send_metrics._extract_command(None)
        assert cmd is None
        assert skill is None

    def test_empty_transcript(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text("")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd is None
        assert skill is None

    def test_malformed_json(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text("not valid json\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd is None
        assert skill is None

    def test_system_message_before_user(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        lines = [
            json.dumps({"role": "system", "content": "system prompt"}),
            json.dumps({"role": "user", "content": "/specify 003"}),
        ]
        transcript.write_text("\n".join(lines) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd == "specify"
        assert skill == "spec-creation"

    def test_respects_line_limit(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        lines = [json.dumps({"role": "system", "content": f"line {i}"}) for i in range(60)]
        lines.append(json.dumps({"role": "user", "content": "/specify 003"}))
        transcript.write_text("\n".join(lines) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd is None
        assert skill is None

    def test_rich_message_format(self, tmp_path):
        """Real Cursor transcript format: message.content[].text."""
        transcript = tmp_path / "transcript.jsonl"
        entry = {
            "role": "user",
            "message": {"content": [{"type": "text", "text": "/specify 003 expand telemetry"}]},
        }
        transcript.write_text(json.dumps(entry) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd == "specify"
        assert skill == "spec-creation"

    def test_user_query_tags(self, tmp_path):
        """Cursor wraps user text in <user_query> tags within system metadata."""
        transcript = tmp_path / "transcript.jsonl"
        entry = {
            "role": "user",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "<cursor_commands>some metadata</cursor_commands>\n"
                            "<user_query>\n/specify 003 expand\n</user_query>"
                        ),
                    }
                ]
            },
        }
        transcript.write_text(json.dumps(entry) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd == "specify"
        assert skill == "spec-creation"

    def test_prefixed_command(self, tmp_path):
        """Commands prefixed with other text like 'make /specify'."""
        transcript = tmp_path / "transcript.jsonl"
        entry = {
            "role": "user",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "<user_query>\nmake /specify 001 for setup\n</user_query>",
                    }
                ]
            },
        }
        transcript.write_text(json.dumps(entry) + "\n")
        cmd, skill = send_metrics._extract_command(str(transcript))
        assert cmd == "specify"
        assert skill == "spec-creation"
