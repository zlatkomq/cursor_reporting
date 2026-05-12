"""Tests for docker-compose.yml structure (T13)."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT / "docker-compose.yml"


@pytest.fixture()
def compose() -> dict:
    """Parse and return the docker-compose.yml as a dict."""
    assert COMPOSE_FILE.exists(), "docker-compose.yml must exist at project root"
    return yaml.safe_load(COMPOSE_FILE.read_text())


class TestComposeFileExists:
    """docker-compose.yml must exist and be valid YAML."""

    def test_file_exists(self) -> None:
        assert COMPOSE_FILE.exists()

    def test_valid_yaml(self) -> None:
        data = yaml.safe_load(COMPOSE_FILE.read_text())
        assert isinstance(data, dict)


class TestServices:
    """Verify api and db services are defined correctly."""

    def test_has_api_service(self, compose: dict) -> None:
        assert "api" in compose["services"]

    def test_has_db_service(self, compose: dict) -> None:
        assert "db" in compose["services"]

    def test_api_build_context(self, compose: dict) -> None:
        api = compose["services"]["api"]
        build = api["build"]
        if isinstance(build, str):
            assert build == "."
        else:
            assert build.get("context") == "."

    def test_api_port_8000(self, compose: dict) -> None:
        api = compose["services"]["api"]
        ports = [str(p) for p in api["ports"]]
        assert any("8000" in p for p in ports)

    def test_api_env_file(self, compose: dict) -> None:
        api = compose["services"]["api"]
        env_file = api["env_file"]
        if isinstance(env_file, list):
            assert ".env" in env_file
        else:
            assert env_file == ".env"

    def test_api_depends_on_db(self, compose: dict) -> None:
        api = compose["services"]["api"]
        depends = api["depends_on"]
        if isinstance(depends, list):
            assert "db" in depends
        else:
            assert "db" in depends
            condition = depends["db"].get("condition")
            assert condition == "service_healthy"

    def test_api_restart_policy(self, compose: dict) -> None:
        api = compose["services"]["api"]
        assert api.get("restart") == "unless-stopped"

    def test_db_image_mariadb(self, compose: dict) -> None:
        db = compose["services"]["db"]
        assert "mariadb" in db["image"]

    def test_db_port_3306(self, compose: dict) -> None:
        db = compose["services"]["db"]
        ports = [str(p) for p in db["ports"]]
        assert any("3306" in p for p in ports)

    def test_db_healthcheck(self, compose: dict) -> None:
        db = compose["services"]["db"]
        assert "healthcheck" in db
        hc = db["healthcheck"]
        assert "test" in hc

    def test_db_volume_mount(self, compose: dict) -> None:
        db = compose["services"]["db"]
        volumes = db.get("volumes", [])
        assert any("mariadb_data" in str(v) and "/var/lib/mysql" in str(v) for v in volumes)


class TestVolumes:
    """Verify named volume is declared."""

    def test_named_volume_defined(self, compose: dict) -> None:
        assert "mariadb_data" in compose.get("volumes", {})
