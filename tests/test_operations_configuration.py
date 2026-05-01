from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_deploy_workflow_uses_self_hosted_windows_runner() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "deploy.yml").read_text(
        encoding="utf-8"
    )

    assert "branches:" in workflow
    assert "- main" in workflow
    assert "self-hosted" in workflow
    assert "Windows" in workflow
    assert ".\\scripts\\deploy.ps1" in workflow
    assert "DISCORD_DEPLOY_WEBHOOK_URL" in workflow
    assert "secrets.DISCORD_DEPLOY_WEBHOOK_URL" in workflow
    assert "PRODUCTION_PROJECT_ROOT" in workflow


def test_production_scripts_include_docker_restart_and_startup_controls() -> None:
    scripts_dir = PROJECT_ROOT / "scripts"

    deploy_script = (scripts_dir / "deploy.ps1").read_text(encoding="utf-8")
    start_script = (scripts_dir / "start-bot.ps1").read_text(encoding="utf-8")
    restart_script = (scripts_dir / "restart-bot.ps1").read_text(encoding="utf-8")
    startup_script = (scripts_dir / "register-startup-task.ps1").read_text(
        encoding="utf-8"
    )

    assert "git pull --ff-only origin main" in deploy_script
    assert "docker compose build app" in deploy_script
    assert "docker compose up -d app" in deploy_script
    assert "docker compose up -d --build app" in start_script
    assert "docker compose restart app" in restart_script
    assert "Register-ScheduledTask" in startup_script


def test_env_example_documents_operational_variables_without_real_values() -> None:
    env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "APP_ENV=development" in env_example
    assert "DISCORD_ALERT_WEBHOOK_URL=" in env_example
    assert "DISCORD_DEPLOY_WEBHOOK_URL=" in env_example
    assert "your_discord_bot_token" not in env_example


def test_operations_document_covers_docker_runner_startup_and_logs() -> None:
    operations_doc = (PROJECT_ROOT / "docs" / "operations.md").read_text(
        encoding="utf-8"
    )

    assert "self-hosted Windows runner" in operations_doc
    assert "Docker Desktop" in operations_doc
    assert ".\\svc.cmd install" in operations_doc
    assert ".\\scripts\\register-startup-task.ps1" in operations_doc
    assert "PRODUCTION_PROJECT_ROOT" in operations_doc
    assert "logs/bot.log" in operations_doc
    assert "docker compose logs -f app" in operations_doc
