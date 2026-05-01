import httpx
import pytest

from app.config import APP_ENV_ENV_NAME, BOT_NAME_ENV_NAME
from app.services import operational_notification_service
from app.services.operational_notification_service import send_operational_notification


class FakeResponse:
    def __init__(self) -> None:
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True


def test_send_operational_notification_posts_to_webhook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request = {}
    response = FakeResponse()
    monkeypatch.setenv(APP_ENV_ENV_NAME, "production")
    monkeypatch.setenv(BOT_NAME_ENV_NAME, "test-bot")

    def fake_post(url: str, json: dict[str, str], timeout: float) -> FakeResponse:
        captured_request["url"] = url
        captured_request["json"] = json
        captured_request["timeout"] = timeout
        return response

    monkeypatch.setattr(operational_notification_service.httpx, "post", fake_post)

    assert send_operational_notification("started", "https://discord.example") is True
    assert captured_request == {
        "url": "https://discord.example",
        "json": {"content": "[production] test-bot: started"},
        "timeout": 5.0,
    }
    assert response.raise_for_status_called is True


def test_send_operational_notification_skips_when_webhook_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DISCORD_ALERT_WEBHOOK_URL", raising=False)

    assert send_operational_notification("started") is False


def test_send_operational_notification_handles_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(url: str, json: dict[str, str], timeout: float) -> httpx.Response:
        raise httpx.ConnectError("failed")

    monkeypatch.setattr(operational_notification_service.httpx, "post", fake_post)

    assert send_operational_notification("started", "https://discord.example") is False
