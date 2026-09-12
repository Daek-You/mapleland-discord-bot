"""Dispatch claimed feed deliveries without blocking Discord's event loop."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.db.delivery_repository import DeliveryRecord

logger = logging.getLogger(__name__)
DEFAULT_DELIVERY_BATCH_SIZE = 20
DEFAULT_DELIVERY_LEASE_DURATION = timedelta(minutes=5)
MAX_DELIVERY_RETRY_DELAY = timedelta(hours=1)


class DeliveryRepository(Protocol):
    """Synchronous persistence operations used by the async dispatcher."""

    def claim_ready(
        self,
        now: datetime,
        *,
        limit: int,
        lease_duration: timedelta,
    ) -> list[DeliveryRecord]: ...

    def mark_sent(
        self,
        delivery_id: int,
        *,
        discord_message_id: str,
        sent_at: datetime,
    ) -> None: ...

    def reschedule(self, delivery_id: int, *, error_kind: str, retry_at: datetime) -> None: ...

    def mark_failed(self, delivery_id: int, *, error_kind: str) -> None: ...


class PermanentDeliveryError(Exception):
    """A send failure that needs user configuration changes, not another retry."""

    def __init__(self, error_kind: str) -> None:
        super().__init__(error_kind)
        self.error_kind = error_kind


@dataclass(frozen=True)
class DispatchResult:
    """Counts produced by one background dispatch pass."""

    sent_count: int = 0
    retried_count: int = 0
    failed_count: int = 0


async def dispatch_ready_deliveries(
    repository: DeliveryRepository,
    send_delivery: Callable[[DeliveryRecord], Awaitable[str]],
    *,
    now: datetime | None = None,
    batch_size: int = DEFAULT_DELIVERY_BATCH_SIZE,
    lease_duration: timedelta = DEFAULT_DELIVERY_LEASE_DURATION,
) -> DispatchResult:
    """Send one leased batch and persist each outcome before moving to the next item."""
    dispatch_started_at = now or datetime.now(UTC)
    deliveries = await asyncio.to_thread(
        repository.claim_ready,
        dispatch_started_at,
        limit=batch_size,
        lease_duration=lease_duration,
    )
    result = DispatchResult()
    for delivery in deliveries:
        try:
            message_id = await send_delivery(delivery)
        except asyncio.CancelledError:
            raise
        except PermanentDeliveryError as error:
            logger.warning("Feed delivery cannot be retried: %s", error.error_kind)
            await asyncio.to_thread(
                repository.mark_failed,
                delivery.id,
                error_kind=error.error_kind,
            )
            result = DispatchResult(
                sent_count=result.sent_count,
                retried_count=result.retried_count,
                failed_count=result.failed_count + 1,
            )
        except Exception:
            retry_at = dispatch_started_at + _get_retry_delay(delivery.attempt_count)
            logger.error("Feed delivery failed and will be retried.", exc_info=True)
            await asyncio.to_thread(
                repository.reschedule,
                delivery.id,
                error_kind="discord_http_error",
                retry_at=retry_at,
            )
            result = DispatchResult(
                sent_count=result.sent_count,
                retried_count=result.retried_count + 1,
                failed_count=result.failed_count,
            )
        else:
            await asyncio.to_thread(
                repository.mark_sent,
                delivery.id,
                discord_message_id=message_id,
                sent_at=dispatch_started_at,
            )
            result = DispatchResult(
                sent_count=result.sent_count + 1,
                retried_count=result.retried_count,
                failed_count=result.failed_count,
            )
    return result


def _get_retry_delay(attempt_count: int) -> timedelta:
    """Use bounded exponential backoff to protect Discord after temporary failures."""
    return min(timedelta(minutes=2 ** max(attempt_count - 1, 0)), MAX_DELIVERY_RETRY_DELAY)
