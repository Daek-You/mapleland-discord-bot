import asyncio
import logging

import discord

import app.bot.client as client_module
from app.bot.client import MapleLandDiscordClient
from app.config import (
    DEFAULT_NOTICE_CHECK_INTERVAL_SECONDS,
    DEFAULT_NOTICE_DATABASE_PATH,
    NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME,
    NOTICE_DATABASE_PATH_ENV_NAME,
    get_notice_check_interval_seconds,
    get_notice_database_path,
)
from app.db.delivery_repository import DeliveryRecord, DeliveryStatus

TEST_NOTICE_CHECK_INTERVAL_SECONDS = 30


def test_get_notice_check_interval_seconds_returns_default(monkeypatch) -> None:
    monkeypatch.delenv(NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME, raising=False)

    assert get_notice_check_interval_seconds() == DEFAULT_NOTICE_CHECK_INTERVAL_SECONDS


def test_get_notice_check_interval_seconds_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME,
        str(TEST_NOTICE_CHECK_INTERVAL_SECONDS),
    )

    assert get_notice_check_interval_seconds() == TEST_NOTICE_CHECK_INTERVAL_SECONDS


def test_get_notice_database_path_returns_default_for_empty_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(NOTICE_DATABASE_PATH_ENV_NAME, "")

    assert get_notice_database_path() == DEFAULT_NOTICE_DATABASE_PATH


def test_notice_notification_loop_continues_after_unexpected_error(
    monkeypatch,
    caplog,
) -> None:
    class LoopHarness:
        def __init__(self) -> None:
            self.attempts = 0

        async def wait_until_ready(self) -> None:
            return None

        def is_closed(self) -> bool:
            return self.attempts >= 2

        async def send_new_notice_notifications(self) -> None:
            self.attempts += 1
            if self.attempts == 1:
                raise RuntimeError("temporary failure")

    async def skip_sleep(seconds: float) -> None:
        return None

    harness = LoopHarness()
    monkeypatch.setattr(client_module.asyncio, "sleep", skip_sleep)

    with caplog.at_level(logging.ERROR):
        asyncio.run(MapleLandDiscordClient._run_notice_notification_loop(harness))

    assert harness.attempts == 2
    assert "Unexpected error in notice notification loop." in caplog.text


def test_close_waits_for_notice_notification_task(monkeypatch) -> None:
    class FakeTimerService:
        def __init__(self) -> None:
            self.cancelled = False

        def cancel_all(self) -> None:
            self.cancelled = True

    class FakeHttpClient:
        def __init__(self) -> None:
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True

    async def scenario() -> None:
        worker_finished = asyncio.Event()
        discord_client_closed = False

        async def worker() -> None:
            try:
                await asyncio.Future()
            finally:
                worker_finished.set()

        async def fake_discord_close(self) -> None:
            nonlocal discord_client_closed
            discord_client_closed = True

        monkeypatch.setattr(
            client_module,
            "create_default_notice_repository",
            lambda: object(),
        )
        monkeypatch.setattr(
            client_module,
            "create_default_delivery_repository",
            lambda: object(),
        )
        monkeypatch.setattr(
            client_module,
            "create_default_subscription_repository",
            lambda: object(),
        )
        http_client = FakeHttpClient()
        monkeypatch.setattr(
            client_module,
            "create_shared_http_client",
            lambda: http_client,
        )
        monkeypatch.setattr(discord.Client, "close", fake_discord_close)

        client = MapleLandDiscordClient()
        timer_service = FakeTimerService()
        client.holy_symbol_timer_service = timer_service
        client.notice_notification_task = asyncio.create_task(worker())
        await asyncio.sleep(0)

        await client.close()

        assert worker_finished.is_set()
        assert client.notice_notification_task is None
        assert timer_service.cancelled is True
        assert http_client.closed is True
        assert discord_client_closed is True

    asyncio.run(scenario())


def test_notice_notification_uses_shared_http_client(monkeypatch) -> None:
    shared_http_client = object()
    captured_fetcher = None

    class LoopHarness:
        http_client = shared_http_client
        notice_repository = object()

        async def collect_latest_feed_notices(self) -> None:
            return None

        def get_channel(self, channel_id: int):
            return object()

    async def collect_notifications(**kwargs):
        nonlocal captured_fetcher
        captured_fetcher = kwargs["fetch_notice_items"]
        return []

    monkeypatch.setattr(client_module, "get_notice_channel_id", lambda: "123")
    monkeypatch.setattr(
        client_module,
        "collect_new_notice_notifications",
        collect_notifications,
    )

    asyncio.run(MapleLandDiscordClient.send_new_notice_notifications(LoopHarness()))

    assert captured_fetcher is not None
    assert captured_fetcher.keywords["client"] is shared_http_client


def test_feed_delivery_dispatch_loop_continues_after_unexpected_error(monkeypatch, caplog) -> None:
    class LoopHarness:
        def __init__(self) -> None:
            self.attempts = 0

        async def wait_until_ready(self) -> None:
            return None

        def is_closed(self) -> bool:
            return self.attempts >= 2

        async def send_pending_feed_deliveries(self) -> None:
            self.attempts += 1
            if self.attempts == 1:
                raise RuntimeError("temporary failure")

    async def skip_sleep(seconds: float) -> None:
        return None

    harness = LoopHarness()
    monkeypatch.setattr(client_module.asyncio, "sleep", skip_sleep)

    with caplog.at_level(logging.ERROR):
        asyncio.run(MapleLandDiscordClient._run_delivery_dispatch_loop(harness))

    assert harness.attempts == 2
    assert "Unexpected error in feed delivery dispatch loop." in caplog.text


def test_format_feed_delivery_includes_optional_role_mention() -> None:
    delivery = DeliveryRecord(
        id=1,
        feed_revision_id=2,
        channel_id="123",
        category="notice",
        title="Patch note",
        url="https://maple.land/board/notices/100",
        content="content",
        role_id="456",
        attempt_count=1,
        status=DeliveryStatus.PROCESSING,
    )

    message = client_module._format_feed_delivery(delivery)

    assert message == "<@&456>\n**[notice] Patch note**\nhttps://maple.land/board/notices/100"
