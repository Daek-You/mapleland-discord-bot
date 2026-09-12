import pytest

from app.config import (
    DISCORD_TOKEN_ENV_NAME,
    NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME,
    get_required_discord_token,
)
from app.main import main


class FakeDiscordClient:
    def __init__(self) -> None:
        self.token: str | None = None

    def run(self, token: str) -> None:
        self.token = token


def test_get_required_discord_token_returns_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DISCORD_TOKEN_ENV_NAME, "test-token")

    assert get_required_discord_token() == "test-token"


def test_get_required_discord_token_requires_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(DISCORD_TOKEN_ENV_NAME, raising=False)

    with pytest.raises(RuntimeError, match="DISCORD_TOKEN"):
        get_required_discord_token()


def test_main_runs_discord_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(DISCORD_TOKEN_ENV_NAME, "test-token")
    client = FakeDiscordClient()

    assert main(lambda: client) is None
    assert client.token == "test-token"


def test_main_rejects_invalid_config_before_creating_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client_factory_called = False

    def client_factory() -> FakeDiscordClient:
        nonlocal client_factory_called
        client_factory_called = True
        return FakeDiscordClient()

    monkeypatch.setenv(DISCORD_TOKEN_ENV_NAME, "test-token")
    monkeypatch.setenv(NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME, "0")

    with pytest.raises(RuntimeError, match=NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME):
        main(client_factory)

    assert client_factory_called is False
