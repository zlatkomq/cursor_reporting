"""Integration tests for Docker Compose full stack (T17)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Iterator

import pytest

COMPOSE_FILE = "docker-compose.yml"
BASE_URL = "http://localhost:8000"
STARTUP_WAIT_SECONDS = 15
_ENV_PATH = Path(".env")

_COMPOSE_ENV: dict[str, str] = {
    "MARIADB_ROOT_PASSWORD": "test-root-pw",
    "MARIADB_DATABASE": "cursor_metrics_test",
    "MARIADB_USER": "test_user",
    "MARIADB_PASSWORD": "test-pw",
    "DATABASE_URL": "mysql+aiomysql://test_user:test-pw@db:3306/cursor_metrics_test",
    "SECRET_KEY": "integration-test-secret-key",
}


def _docker_available() -> bool:
    """Return True if the Docker daemon is reachable."""
    docker = shutil.which("docker")
    if docker is None:
        return False
    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        timeout=10,
    )
    return result.returncode == 0


def _compose_env() -> dict[str, str]:
    """Return an environment dict with required compose variables injected."""
    return {**os.environ, **_COMPOSE_ENV}


def _compose_run(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_compose_env(),
    )


def _write_dotenv() -> bool:
    """Write a .env file with test values. Returns True if a new file was created."""
    if _ENV_PATH.exists():
        return False
    lines = [f"{k}={v}" for k, v in _COMPOSE_ENV.items()]
    _ENV_PATH.write_text("\n".join(lines) + "\n")
    return True


def _remove_dotenv(created: bool) -> None:
    if created:
        _ENV_PATH.unlink(missing_ok=True)


@pytest.fixture()
def _dotenv_file() -> Iterator[None]:
    """Create a temporary .env in the project root so docker compose config succeeds."""
    created = _write_dotenv()
    yield
    _remove_dotenv(created)


class TestComposeConfig:
    """Validate docker-compose.yml syntax without requiring the Docker daemon."""

    @pytest.mark.usefixtures("_dotenv_file")
    def test_compose_config_valid(self) -> None:
        result = _compose_run("config", "--quiet")
        assert result.returncode == 0, f"docker compose config failed:\n{result.stderr}"


@pytest.mark.integration
class TestDockerComposeStack:
    """End-to-end tests that bring up the full stack via Docker Compose."""

    _stack_up: ClassVar[bool] = False
    _created_env: ClassVar[bool] = False

    @classmethod
    def _start_stack(cls) -> None:
        if cls._stack_up:
            return
        cls._created_env = _write_dotenv()
        result = _compose_run("up", "-d", "--build", timeout=180)
        if result.returncode != 0:
            _remove_dotenv(cls._created_env)
            pytest.skip(f"docker compose up failed:\n{result.stderr}")
        time.sleep(STARTUP_WAIT_SECONDS)
        cls._stack_up = True

    @classmethod
    def _stop_stack(cls) -> None:
        if cls._stack_up:
            _compose_run("down", "-v", timeout=60)
            cls._stack_up = False
        _remove_dotenv(cls._created_env)

    @classmethod
    def setup_class(cls) -> None:
        if not _docker_available():
            pytest.skip("Docker daemon not available")
        cls._start_stack()

    @classmethod
    def teardown_class(cls) -> None:
        cls._stop_stack()

    def _curl(
        self,
        path: str,
        *,
        method: str = "GET",
        json_body: dict[str, object] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        cmd = ["curl", "-s", "-X", method, f"{BASE_URL}{path}"]
        if json_body is not None:
            cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(json_body)])
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    def test_health_endpoint_responds(self) -> None:
        result = self._curl("/")
        assert result.returncode == 0, f"curl failed:\n{result.stderr}"
        body = json.loads(result.stdout)
        assert body["status"] == "ok"
        assert "version" in body
        assert "database" in body

    def test_ingest_endpoint_accepts(self) -> None:
        payload: dict[str, object] = {
            "event_type": "stop",
            "conversation_id": "conv-integration-001",
            "generation_id": "gen-integration-001",
            "model": "claude-4-opus",
            "user_email": "integration@test.com",
            "status": "completed",
            "timestamp": "2026-05-12T10:00:00Z",
        }
        result = self._curl("/api/v1/ingest", method="POST", json_body=payload)
        assert result.returncode == 0, f"curl failed:\n{result.stderr}"
        body = json.loads(result.stdout)
        assert body["status"] == "accepted"
