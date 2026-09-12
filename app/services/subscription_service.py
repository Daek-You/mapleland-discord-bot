"""Business operations for feed category subscriptions."""

from __future__ import annotations

import asyncio
from typing import Protocol


class SubscriptionRepository(Protocol):
    """Synchronous subscription persistence used by command handlers."""

    def save(self, *, category: str, channel_id: str, role_id: str | None = None) -> None: ...

    def disable(self, *, category: str, channel_id: str) -> bool: ...


async def subscribe_to_feed(
    repository: SubscriptionRepository,
    *,
    category: str,
    channel_id: str,
    role_id: str | None,
) -> None:
    """Persist one enabled category subscription off the Discord event loop."""
    await asyncio.to_thread(
        repository.save,
        category=category,
        channel_id=channel_id,
        role_id=role_id,
    )


async def unsubscribe_from_feed(
    repository: SubscriptionRepository,
    *,
    category: str,
    channel_id: str,
) -> bool:
    """Disable one category subscription off the Discord event loop."""
    return await asyncio.to_thread(
        repository.disable,
        category=category,
        channel_id=channel_id,
    )
