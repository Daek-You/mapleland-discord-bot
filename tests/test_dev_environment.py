from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_includes_pytest() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    dev_dependencies = pyproject["dependency-groups"]["dev"]

    assert any(dependency.startswith("pytest") for dependency in dev_dependencies)


def test_docker_configuration_uses_python_311_slim_and_uv() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text()
    compose_file = (PROJECT_ROOT / "docker-compose.yml").read_text()

    assert "FROM python:3.11-slim" in dockerfile
    assert "UV_PROJECT_ENVIRONMENT=/opt/venv" in dockerfile
    assert "uv sync --dev" in dockerfile
    assert "uv run pytest" in compose_file
