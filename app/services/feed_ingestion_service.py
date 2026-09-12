"""Store collected feed items and queue deliveries for active subscriptions."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol
from urllib.parse import urlparse

from app.crawler.mapleland import MaplelandCrawlerError, NoticeItem, fetch_latest_notice_items
from app.db.feed_repository import FeedChange, FeedItemRecord, FeedSaveResult
from app.db.subscription_repository import FeedSubscription


class FeedRepository(Protocol):
    """Persistence operations needed to normalize a collected item."""

    def save(self, item: FeedItemRecord) -> FeedSaveResult: ...

    def has_items(self, *, source: str, category: str) -> bool: ...


class SubscriptionRepository(Protocol):
    """Persistence operations needed to find notification targets."""

    def list_enabled(self, *, category: str) -> list[FeedSubscription]: ...


class DeliveryRepository(Protocol):
    """Persistence operation needed to queue an idempotent delivery."""

    def enqueue(
        self,
        feed_revision_id: int,
        channel_id: str,
        *,
        role_id: str | None = None,
    ) -> bool: ...


@dataclass(frozen=True)
class FeedIngestionResult:
    """The detected content change and number of newly queued deliveries."""

    change: FeedChange
    queued_delivery_count: int


async def ingest_feed_item(
    item: FeedItemRecord,
    *,
    feed_repository: FeedRepository,
    subscription_repository: SubscriptionRepository,
    delivery_repository: DeliveryRepository,
    queue_deliveries: bool = True,
) -> FeedIngestionResult:
    """Save one feed item and queue each subscribed channel exactly once."""
    return await asyncio.to_thread(
        _ingest_feed_item,
        item,
        feed_repository,
        subscription_repository,
        delivery_repository,
        queue_deliveries,
    )


def _ingest_feed_item(
    item: FeedItemRecord,
    feed_repository: FeedRepository,
    subscription_repository: SubscriptionRepository,
    delivery_repository: DeliveryRepository,
    queue_deliveries: bool,
) -> FeedIngestionResult:
    save_result = feed_repository.save(item)
    if save_result.revision_id is None or not queue_deliveries:
        return FeedIngestionResult(change=save_result.change, queued_delivery_count=0)

    queued_delivery_count = 0
    for subscription in subscription_repository.list_enabled(category=item.category):
        if delivery_repository.enqueue(
            save_result.revision_id,
            subscription.channel_id,
            role_id=subscription.role_id,
        ):
            queued_delivery_count += 1
    return FeedIngestionResult(
        change=save_result.change,
        queued_delivery_count=queued_delivery_count,
    )


async def collect_notice_feed_updates(
    fetch_notice_items=fetch_latest_notice_items,
    *,
    feed_repository: FeedRepository,
    subscription_repository: SubscriptionRepository,
    delivery_repository: DeliveryRepository,
) -> list[FeedIngestionResult]:
    """Normalize official notices and queue updates after the initial baseline pass."""
    try:
        notice_items = await fetch_notice_items()
    except MaplelandCrawlerError:
        return []

    is_initialized = await asyncio.to_thread(
        feed_repository.has_items,
        source="mapleland",
        category="notice",
    )
    results: list[FeedIngestionResult] = []
    for notice_item in notice_items:
        results.append(
            await ingest_feed_item(
                _notice_item_to_feed_record(notice_item),
                feed_repository=feed_repository,
                subscription_repository=subscription_repository,
                delivery_repository=delivery_repository,
                queue_deliveries=is_initialized,
            )
        )
    return results


def _notice_item_to_feed_record(notice_item: NoticeItem) -> FeedItemRecord:
    content = f"{notice_item.title}\n{notice_item.url}"
    external_id = urlparse(notice_item.url).path.rstrip("/").split("/")[-1]
    return FeedItemRecord(
        source="mapleland",
        category="notice",
        external_id=external_id or notice_item.url,
        url=notice_item.url,
        title=notice_item.title,
        content_hash=sha256(content.encode()).hexdigest(),
        content=content,
    )
