import pytest

from app.config import (
    APP_ENV_ENV_NAME,
    BOT_NAME_ENV_NAME,
    DEFAULT_APP_ENV,
    DEFAULT_BOT_NAME,
    DISCORD_ALERT_WEBHOOK_URL_ENV_NAME,
    DISCORD_GUILD_ID_ENV_NAME,
    DISCORD_TOKEN_ENV_NAME,
    LOG_LEVEL_ENV_NAME,
    LOG_TIMEZONE_ENV_NAME,
    NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME,
    get_app_env,
    get_bot_name,
    get_discord_alert_webhook_url,
    get_notice_check_interval_seconds,
    validate_runtime_config,
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


@pytest.mark.parametrize("value", ["0", "-1", "not-a-number"])
def test_get_notice_check_interval_seconds_rejects_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv(NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME, value)

    with pytest.raises(RuntimeError, match=NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME):
        get_notice_check_interval_seconds()


def test_validate_runtime_config_accepts_defaults_with_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(DISCORD_TOKEN_ENV_NAME, "test-token")
    monkeypatch.delenv(DISCORD_GUILD_ID_ENV_NAME, raising=False)

    assert validate_runtime_config() is None


@pytest.mark.parametrize("value", ["0", "-10", "abc", "1.5"])
def test_validate_runtime_config_rejects_invalid_discord_id(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv(DISCORD_TOKEN_ENV_NAME, "test-token")
    monkeypatch.setenv(DISCORD_GUILD_ID_ENV_NAME, value)

    with pytest.raises(RuntimeError, match=DISCORD_GUILD_ID_ENV_NAME):
        validate_runtime_config()


def test_validate_runtime_config_rejects_invalid_log_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(DISCORD_TOKEN_ENV_NAME, "test-token")
    monkeypatch.setenv(LOG_LEVEL_ENV_NAME, "VERBOSE")

    with pytest.raises(RuntimeError, match=LOG_LEVEL_ENV_NAME):
        validate_runtime_config()


def test_validate_runtime_config_rejects_invalid_timezone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(DISCORD_TOKEN_ENV_NAME, "test-token")
    monkeypatch.setenv(LOG_TIMEZONE_ENV_NAME, "Mars/Olympus")

    with pytest.raises(RuntimeError, match=LOG_TIMEZONE_ENV_NAME):
        validate_runtime_config()
