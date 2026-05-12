"""Tests for Dockerfile and .dockerignore structure (T12)."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"


class TestDockerfile:
    """Verify Dockerfile exists and has expected multi-stage structure."""

    @pytest.fixture()
    def content(self) -> str:
        assert DOCKERFILE.exists(), "Dockerfile must exist at project root"
        return DOCKERFILE.read_text()

    def test_dockerfile_exists(self) -> None:
        assert DOCKERFILE.exists()

    def test_base_image_python312(self, content: str) -> None:
        assert "python:3.12" in content

    def test_multi_stage_build(self, content: str) -> None:
        from_count = sum(1 for line in content.splitlines() if line.strip().upper().startswith("FROM"))
        assert from_count >= 2, "Dockerfile must use multi-stage build (>=2 FROM statements)"

    def test_expose_8000(self, content: str) -> None:
        assert any(line.strip().upper().startswith("EXPOSE") and "8000" in line for line in content.splitlines()), (
            "Dockerfile must EXPOSE 8000"
        )

    def test_uvicorn_entrypoint(self, content: str) -> None:
        lower = content.lower()
        assert "uvicorn" in lower, "Dockerfile must reference uvicorn in CMD or ENTRYPOINT"
        assert "cursor_metrics.main:app" in content, "Dockerfile must use correct app entrypoint"

    def test_non_root_user(self, content: str) -> None:
        lower = content.lower()
        has_useradd = "useradd" in lower or "adduser" in lower or "addgroup" in lower
        has_user = any(line.strip().upper().startswith("USER") for line in content.splitlines())
        assert has_useradd and has_user, "Dockerfile must create and switch to a non-root user"

    def test_no_dev_dependencies_flag(self, content: str) -> None:
        assert "--no-dev" in content, "Dockerfile must install only production dependencies (--no-dev)"

    def test_uv_used_in_build(self, content: str) -> None:
        assert "uv" in content.lower(), "Dockerfile must use uv for dependency resolution"


class TestDockerignore:
    """Verify .dockerignore exists and excludes expected paths."""

    @pytest.fixture()
    def content(self) -> str:
        assert DOCKERIGNORE.exists(), ".dockerignore must exist at project root"
        return DOCKERIGNORE.read_text()

    def test_dockerignore_exists(self) -> None:
        assert DOCKERIGNORE.exists()

    @pytest.mark.parametrize(
        "pattern",
        [".git", "tests/", ".venv/", ".worktrees/", "__pycache__/"],
    )
    def test_excludes_pattern(self, content: str, pattern: str) -> None:
        lines = [line.strip() for line in content.splitlines()]
        assert any(pattern in line for line in lines), f".dockerignore must exclude {pattern}"
