from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_includes_pytest() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    dev_dependencies = pyproject["dependency-groups"]["dev"]

    assert any(dependency.startswith("pytest") for dependency in dev_dependencies)


def test_local_python_version_matches_docker_runtime() -> None:
    python_version = (PROJECT_ROOT / ".python-version").read_text().strip()
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()

    assert python_version == "3.11"
    assert f"FROM python:{python_version}-slim" in dockerfile


def test_docker_configuration_uses_python_311_slim_and_uv() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
    compose_file = (PROJECT_ROOT / "docker-compose.yml").read_text()
    production_compose_file = (PROJECT_ROOT / "docker-compose.prod.yml").read_text()

    assert "FROM python:3.11-slim" in dockerfile
    assert "UV_PROJECT_ENVIRONMENT=/opt/venv" in dockerfile
    assert "uv sync --dev" in dockerfile
    assert "uv run pytest" in compose_file
    assert "APP_ENV" in compose_file
    assert "BOT_NAME" in compose_file
    assert "DISCORD_ALERT_WEBHOOK_URL" in compose_file
    assert "NOTICE_CHANNEL_ID" in compose_file
    assert "NOTICE_CHECK_INTERVAL_SECONDS" in compose_file
    assert "NOTICE_DATABASE_PATH" in compose_file
    assert "restart: unless-stopped" in production_compose_file
    assert ".env.production" in production_compose_file
    assert "uv run python -m app.main" in production_compose_file
