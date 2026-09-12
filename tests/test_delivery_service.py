import asyncio
from datetime import UTC, datetime, timedelta

from app.db.delivery_repository import DeliveryRecord, DeliveryStatus
from app.services.delivery_service import (
    DispatchResult,
    PermanentDeliveryError,
    dispatch_ready_deliveries,
)


class FakeDeliveryRepository:
    def __init__(self, deliveries: list[DeliveryRecord]) -> None:
        self.deliveries = deliveries
        self.sent: list[tuple[int, str]] = []
        self.retried: list[tuple[int, str, datetime]] = []
        self.failed: list[tuple[int, str]] = []

    def claim_ready(self, now, *, limit, lease_duration):
        return self.deliveries[:limit]

    def mark_sent(self, delivery_id, *, discord_message_id, sent_at):
        self.sent.append((delivery_id, discord_message_id))

    def reschedule(self, delivery_id, *, error_kind, retry_at):
        self.retried.append((delivery_id, error_kind, retry_at))

    def mark_failed(self, delivery_id, *, error_kind):
        self.failed.append((delivery_id, error_kind))


def make_delivery(attempt_count: int = 1) -> DeliveryRecord:
    return DeliveryRecord(
        id=1,
        feed_revision_id=2,
        channel_id="123",
        category="notice",
        title="Notice",
        url="https://maple.land/board/notices/100",
        content="Content",
        role_id=None,
        attempt_count=attempt_count,
        status=DeliveryStatus.PROCESSING,
    )


def test_dispatch_marks_successful_delivery_as_sent() -> None:
    repository = FakeDeliveryRepository([make_delivery()])
    now = datetime(2030, 9, 12, 10, 0, tzinfo=UTC)

    result = asyncio.run(
        dispatch_ready_deliveries(repository, lambda delivery: _return("456"), now=now)
    )

    assert result == DispatchResult(sent_count=1)
    assert repository.sent == [(1, "456")]


def test_dispatch_reschedules_temporary_failure_with_exponential_backoff() -> None:
    repository = FakeDeliveryRepository([make_delivery(attempt_count=3)])
    now = datetime(2030, 9, 12, 10, 0, tzinfo=UTC)

    result = asyncio.run(
        dispatch_ready_deliveries(repository, _raise_temporary_error, now=now)
    )

    assert result == DispatchResult(retried_count=1)
    assert repository.retried == [(1, "discord_http_error", now + timedelta(minutes=4))]


def test_dispatch_marks_permanent_failure_without_retry() -> None:
    repository = FakeDeliveryRepository([make_delivery()])

    result = asyncio.run(dispatch_ready_deliveries(repository, _raise_permanent_error))

    assert result == DispatchResult(failed_count=1)
    assert repository.failed == [(1, "channel_not_found")]
    assert repository.retried == []


async def _return(value: str) -> str:
    return value


async def _raise_temporary_error(delivery: DeliveryRecord) -> str:
    raise RuntimeError("temporary")


async def _raise_permanent_error(delivery: DeliveryRecord) -> str:
    raise PermanentDeliveryError("channel_not_found")
