import pytest

from app.main import get_required_discord_token, main


class FakeDiscordClient:
    def __init__(self) -> None:
        self.token: str | None = None

    def run(self, token: str) -> None:
        self.token = token


def test_get_required_discord_token_returns_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")

    assert get_required_discord_token() == "test-token"


def test_get_required_discord_token_requires_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="DISCORD_TOKEN"):
        get_required_discord_token()


def test_main_runs_discord_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    client = FakeDiscordClient()

    assert main(lambda: client) is None
    assert client.token == "test-token"
