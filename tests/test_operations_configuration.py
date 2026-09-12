from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_runs_tests_on_github_hosted_runner() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "ubuntu-latest" in workflow
    assert "uv run ruff check app tests" in workflow
    assert "uv run pytest -v" in workflow


def test_deploy_workflow_uses_production_self_hosted_windows_runner() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "deploy.yml").read_text(
        encoding="utf-8"
    )

    assert "branches:" in workflow
    assert "- main" in workflow
    assert "self-hosted" in workflow
    assert "Windows" in workflow
    assert "production" in workflow
    assert ".\\scripts\\deploy.ps1" in workflow
    assert "DISCORD_DEPLOY_WEBHOOK_URL" in workflow
    assert "secrets.DISCORD_DEPLOY_WEBHOOK_URL" in workflow
    assert "PRODUCTION_PROJECT_ROOT" in workflow


def test_production_scripts_use_production_compose_file_and_env() -> None:
    scripts_dir = PROJECT_ROOT / "scripts"

    deploy_script = (scripts_dir / "deploy.ps1").read_text(encoding="utf-8")
    start_script = (scripts_dir / "start-bot.ps1").read_text(encoding="utf-8")
    stop_script = (scripts_dir / "stop-bot.ps1").read_text(encoding="utf-8")
    restart_script = (scripts_dir / "restart-bot.ps1").read_text(encoding="utf-8")
    startup_script = (scripts_dir / "register-startup-task.ps1").read_text(
        encoding="utf-8"
    )

    assert ".env.production is required" in deploy_script
    assert "git pull --ff-only origin main" in deploy_script
    assert "docker compose -f docker-compose.prod.yml build app" in deploy_script
    assert "docker compose -f docker-compose.prod.yml up -d app" in deploy_script
    assert "docker compose -f docker-compose.prod.yml up -d --build app" in start_script
    assert "docker compose -f docker-compose.prod.yml stop app" in stop_script
    assert "docker compose -f docker-compose.prod.yml up -d --build app" in restart_script
    assert "Register-ScheduledTask" in startup_script


def test_env_examples_document_separate_dev_and_production_variables() -> None:
    dev_env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    production_env_example = (PROJECT_ROOT / ".env.production.example").read_text(
        encoding="utf-8"
    )
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "APP_ENV=development" in dev_env_example
    assert "APP_ENV=production" in production_env_example
    assert "DISCORD_DEPLOY_WEBHOOK_URL=" not in dev_env_example
    assert "DISCORD_DEPLOY_WEBHOOK_URL=" in production_env_example
    assert "your_discord_bot_token" not in dev_env_example
    assert "your_discord_bot_token" not in production_env_example
    assert ".env.*" in gitignore
    assert "!.env.production.example" in gitignore


def test_operations_document_covers_separated_docker_runner_startup_and_logs() -> None:
    operations_doc = (PROJECT_ROOT / "docs" / "operations.md").read_text(
        encoding="utf-8"
    )

    assert "docker-compose.prod.yml" in operations_doc
    assert ".env.production" in operations_doc
    assert "self-hosted Windows runner" in operations_doc
    assert "`production` label" in operations_doc
    assert "Docker Desktop" in operations_doc
    assert ".\\svc.cmd install" in operations_doc
    assert ".\\scripts\\register-startup-task.ps1" in operations_doc
    assert "PRODUCTION_PROJECT_ROOT" in operations_doc
    assert "logs/bot.log" in operations_doc
    assert "docker compose -f docker-compose.prod.yml logs -f app" in operations_doc
