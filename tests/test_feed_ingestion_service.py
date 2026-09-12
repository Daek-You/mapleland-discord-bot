import asyncio
import threading

from app.crawler.mapleland import MaplelandCrawlerError, NoticeItem
from app.db.feed_repository import FeedChange, FeedItemRecord, FeedSaveResult
from app.db.subscription_repository import FeedSubscription
from app.services.feed_ingestion_service import (
    FeedIngestionResult,
    collect_notice_feed_updates,
    ingest_feed_item,
)


class FakeFeedRepository:
    def __init__(self, save_result: FeedSaveResult) -> None:
        self.save_result = save_result
        self.items: list[FeedItemRecord] = []
        self.thread_ids: list[int] = []
        self.initialized = True

    def save(self, item: FeedItemRecord) -> FeedSaveResult:
        self.thread_ids.append(threading.get_ident())
        self.items.append(item)
        return self.save_result

    def has_items(self, *, source: str, category: str) -> bool:
        return self.initialized


class FakeSubscriptionRepository:
    def __init__(self, subscriptions: list[FeedSubscription]) -> None:
        self.subscriptions = subscriptions
        self.categories: list[str] = []

    def list_enabled(self, *, category: str) -> list[FeedSubscription]:
        self.categories.append(category)
        return self.subscriptions


class FakeDeliveryRepository:
    def __init__(self) -> None:
        self.enqueued: list[tuple[int, str, str | None]] = []

    def enqueue(self, feed_revision_id, channel_id, *, role_id=None) -> bool:
        self.enqueued.append((feed_revision_id, channel_id, role_id))
        return True


def make_item() -> FeedItemRecord:
    return FeedItemRecord(
        source="mapleland",
        category="notice",
        external_id="100",
        url="https://maple.land/board/notices/100",
        title="Notice",
        content_hash="hash-v1",
        content="Content",
    )


def test_ingest_new_item_queues_each_enabled_subscription() -> None:
    feed_repository = FakeFeedRepository(
        FeedSaveResult(item_id=1, change=FeedChange.NEW, revision_id=2)
    )
    subscription_repository = FakeSubscriptionRepository(
        [
            FeedSubscription(id=1, category="notice", channel_id="123", role_id="456"),
            FeedSubscription(id=2, category="notice", channel_id="789", role_id=None),
        ]
    )
    delivery_repository = FakeDeliveryRepository()

    result = asyncio.run(
        ingest_feed_item(
            make_item(),
            feed_repository=feed_repository,
            subscription_repository=subscription_repository,
            delivery_repository=delivery_repository,
        )
    )

    assert result == FeedIngestionResult(change=FeedChange.NEW, queued_delivery_count=2)
    assert delivery_repository.enqueued == [(2, "123", "456"), (2, "789", None)]
    assert subscription_repository.categories == ["notice"]


def test_ingest_unchanged_item_does_not_query_or_queue_subscriptions() -> None:
    feed_repository = FakeFeedRepository(
        FeedSaveResult(item_id=1, change=FeedChange.UNCHANGED, revision_id=None)
    )
    subscription_repository = FakeSubscriptionRepository([])
    delivery_repository = FakeDeliveryRepository()

    result = asyncio.run(
        ingest_feed_item(
            make_item(),
            feed_repository=feed_repository,
            subscription_repository=subscription_repository,
            delivery_repository=delivery_repository,
        )
    )

    assert result == FeedIngestionResult(change=FeedChange.UNCHANGED, queued_delivery_count=0)
    assert subscription_repository.categories == []
    assert delivery_repository.enqueued == []


def test_collect_notice_feed_updates_establishes_baseline_without_queuing() -> None:
    feed_repository = FakeFeedRepository(
        FeedSaveResult(item_id=1, change=FeedChange.NEW, revision_id=2)
    )
    feed_repository.initialized = False
    delivery_repository = FakeDeliveryRepository()

    async def fetch_notice_items():
        return [NoticeItem(title="Notice", url="https://maple.land/board/notices/100")]

    results = asyncio.run(
        collect_notice_feed_updates(
            fetch_notice_items,
            feed_repository=feed_repository,
            subscription_repository=FakeSubscriptionRepository(
                [FeedSubscription(id=1, category="notice", channel_id="123", role_id=None)]
            ),
            delivery_repository=delivery_repository,
        )
    )

    assert results == [FeedIngestionResult(change=FeedChange.NEW, queued_delivery_count=0)]
    assert delivery_repository.enqueued == []


def test_collect_notice_feed_updates_queues_after_baseline() -> None:
    feed_repository = FakeFeedRepository(
        FeedSaveResult(item_id=1, change=FeedChange.NEW, revision_id=2)
    )
    delivery_repository = FakeDeliveryRepository()

    async def fetch_notice_items():
        return [NoticeItem(title="Notice", url="https://maple.land/board/notices/100")]

    asyncio.run(
        collect_notice_feed_updates(
            fetch_notice_items,
            feed_repository=feed_repository,
            subscription_repository=FakeSubscriptionRepository(
                [FeedSubscription(id=1, category="notice", channel_id="123", role_id=None)]
            ),
            delivery_repository=delivery_repository,
        )
    )

    assert delivery_repository.enqueued == [(2, "123", None)]


def test_collect_notice_feed_updates_returns_empty_on_crawler_error() -> None:
    async def raise_crawler_error():
        raise MaplelandCrawlerError("failed")

    results = asyncio.run(
        collect_notice_feed_updates(
            raise_crawler_error,
            feed_repository=FakeFeedRepository(
                FeedSaveResult(item_id=1, change=FeedChange.NEW, revision_id=2)
            ),
            subscription_repository=FakeSubscriptionRepository([]),
            delivery_repository=FakeDeliveryRepository(),
        )
    )

    assert results == []


def test_ingest_runs_sync_database_operations_in_worker_thread() -> None:
    event_loop_thread_id = threading.get_ident()
    feed_repository = FakeFeedRepository(
        FeedSaveResult(item_id=1, change=FeedChange.NEW, revision_id=2)
    )

    asyncio.run(
        ingest_feed_item(
            make_item(),
            feed_repository=feed_repository,
            subscription_repository=FakeSubscriptionRepository([]),
            delivery_repository=FakeDeliveryRepository(),
        )
    )

    assert feed_repository.thread_ids
    assert all(thread_id != event_loop_thread_id for thread_id in feed_repository.thread_ids)
