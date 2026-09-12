import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from app.db.delivery_repository import DeliveryStatus, SqliteDeliveryRepository
from app.db.feed_repository import FeedItemRecord, SqliteFeedRepository


def make_revision_id(database_path) -> int:
    feed_repository = SqliteFeedRepository(str(database_path))
    result = feed_repository.save(
        FeedItemRecord(
            source="mapleland",
            category="notice",
            external_id="100",
            url="https://maple.land/board/notices/100",
            title="notice",
            content_hash="hash-v1",
            content="content",
        )
    )
    assert result.revision_id is not None
    return result.revision_id


def test_enqueue_is_idempotent_per_revision_and_channel(tmp_path) -> None:
    database_path = tmp_path / "delivery.sqlite3"
    revision_id = make_revision_id(database_path)
    repository = SqliteDeliveryRepository(str(database_path))

    first = repository.enqueue(revision_id, "123")
    duplicate = repository.enqueue(revision_id, "123")
    another_channel = repository.enqueue(revision_id, "456")

    assert first is True
    assert duplicate is False
    assert another_channel is True


def test_claim_ready_delivery_marks_processing_and_increments_attempt_count(tmp_path) -> None:
    database_path = tmp_path / "delivery.sqlite3"
    revision_id = make_revision_id(database_path)
    repository = SqliteDeliveryRepository(str(database_path))
    repository.enqueue(revision_id, "123")
    now = datetime(2030, 9, 12, 10, 0, tzinfo=UTC)

    deliveries = repository.claim_ready(now, limit=10, lease_duration=timedelta(minutes=5))

    assert len(deliveries) == 1
    assert deliveries[0].channel_id == "123"
    assert deliveries[0].attempt_count == 1
    assert deliveries[0].status is DeliveryStatus.PROCESSING
    assert repository.claim_ready(now, limit=10, lease_duration=timedelta(minutes=5)) == []


def test_expired_lease_can_be_claimed_again(tmp_path) -> None:
    database_path = tmp_path / "delivery.sqlite3"
    revision_id = make_revision_id(database_path)
    repository = SqliteDeliveryRepository(str(database_path))
    repository.enqueue(revision_id, "123")
    now = datetime(2030, 9, 12, 10, 0, tzinfo=UTC)
    first_claim = repository.claim_ready(now, limit=10, lease_duration=timedelta(minutes=5))

    second_claim = repository.claim_ready(
        now + timedelta(minutes=6), limit=10, lease_duration=timedelta(minutes=5)
    )

    assert second_claim[0].id == first_claim[0].id
    assert second_claim[0].attempt_count == 2


def test_rescheduled_delivery_waits_until_retry_time(tmp_path) -> None:
    database_path = tmp_path / "delivery.sqlite3"
    revision_id = make_revision_id(database_path)
    repository = SqliteDeliveryRepository(str(database_path))
    repository.enqueue(revision_id, "123")
    now = datetime(2030, 9, 12, 10, 0, tzinfo=UTC)
    delivery = repository.claim_ready(now, limit=10, lease_duration=timedelta(minutes=5))[0]
    retry_at = now + timedelta(minutes=2)

    repository.reschedule(delivery.id, error_kind="http_exception", retry_at=retry_at)

    assert repository.claim_ready(
        now + timedelta(minutes=1), limit=10, lease_duration=timedelta(minutes=5)
    ) == []
    retried = repository.claim_ready(retry_at, limit=10, lease_duration=timedelta(minutes=5))
    assert retried[0].id == delivery.id
    assert retried[0].attempt_count == 2


def test_mark_sent_finishes_processing_delivery(tmp_path) -> None:
    database_path = tmp_path / "delivery.sqlite3"
    revision_id = make_revision_id(database_path)
    repository = SqliteDeliveryRepository(str(database_path))
    repository.enqueue(revision_id, "123")
    now = datetime(2030, 9, 12, 10, 0, tzinfo=UTC)
    delivery = repository.claim_ready(now, limit=10, lease_duration=timedelta(minutes=5))[0]

    repository.mark_sent(delivery.id, discord_message_id="987", sent_at=now)

    assert repository.claim_ready(
        now + timedelta(days=1), limit=10, lease_duration=timedelta(minutes=5)
    ) == []


def test_enqueue_requires_existing_feed_revision(tmp_path) -> None:
    repository = SqliteDeliveryRepository(str(tmp_path / "delivery.sqlite3"))

    with pytest.raises(sqlite3.IntegrityError):
        repository.enqueue(999, "123")
