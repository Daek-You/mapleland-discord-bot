import pytest

from app.config import (
    APP_ENV_ENV_NAME,
    BOT_NAME_ENV_NAME,
    DEFAULT_APP_ENV,
    DEFAULT_BOT_NAME,
    DISCORD_ALERT_WEBHOOK_URL_ENV_NAME,
    get_app_env,
    get_bot_name,
    get_discord_alert_webhook_url,
)


def test_get_app_env_defaults_to_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(APP_ENV_ENV_NAME, raising=False)

    assert get_app_env() == DEFAULT_APP_ENV


def test_get_app_env_accepts_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(APP_ENV_ENV_NAME, "production")

    assert get_app_env() == "production"


def test_get_app_env_rejects_unknown_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(APP_ENV_ENV_NAME, "staging")

    with pytest.raises(RuntimeError, match="APP_ENV"):
        get_app_env()


def test_get_bot_name_uses_safe_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(BOT_NAME_ENV_NAME, raising=False)

    assert get_bot_name() == DEFAULT_BOT_NAME


def test_get_discord_alert_webhook_url_reads_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(DISCORD_ALERT_WEBHOOK_URL_ENV_NAME, "https://discord.example")

    assert get_discord_alert_webhook_url() == "https://discord.example"
