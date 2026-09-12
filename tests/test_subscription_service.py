import asyncio
import threading

from app.services.subscription_service import subscribe_to_feed, unsubscribe_from_feed


class FakeSubscriptionRepository:
    def __init__(self) -> None:
        self.saved: list[tuple[str, str, str | None]] = []
        self.disabled: list[tuple[str, str]] = []
        self.thread_ids: list[int] = []

    def save(self, *, category: str, channel_id: str, role_id: str | None = None) -> None:
        self.thread_ids.append(threading.get_ident())
        self.saved.append((category, channel_id, role_id))

    def disable(self, *, category: str, channel_id: str) -> bool:
        self.thread_ids.append(threading.get_ident())
        self.disabled.append((category, channel_id))
        return True


def test_subscribe_to_feed_persists_setting_in_worker_thread() -> None:
    repository = FakeSubscriptionRepository()
    event_loop_thread_id = threading.get_ident()

    asyncio.run(
        subscribe_to_feed(
            repository,
            category="notice",
            channel_id="123",
            role_id="456",
        )
    )

    assert repository.saved == [("notice", "123", "456")]
    assert repository.thread_ids == [thread_id for thread_id in repository.thread_ids if thread_id != event_loop_thread_id]


def test_unsubscribe_from_feed_disables_setting_in_worker_thread() -> None:
    repository = FakeSubscriptionRepository()

    was_enabled = asyncio.run(
        unsubscribe_from_feed(repository, category="notice", channel_id="123")
    )

    assert was_enabled is True
    assert repository.disabled == [("notice", "123")]
