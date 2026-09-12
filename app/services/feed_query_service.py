"""Format stored feed categories for Discord slash-command responses."""

from __future__ import annotations

import asyncio
from typing import Protocol

from app.db.feed_repository import FeedSummary

DEFAULT_FEED_DISPLAY_LIMIT = 5


class FeedRepository(Protocol):
    """Read operations used by the Discord feed commands."""

    def list_latest(self, *, category: str, limit: int) -> list[FeedSummary]: ...


async def get_latest_feed_message(
    repository: FeedRepository,
    *,
    category: str,
    heading: str,
    limit: int = DEFAULT_FEED_DISPLAY_LIMIT,
) -> str:
    """Read and format the latest stored items without blocking the event loop."""
    items = await asyncio.to_thread(repository.list_latest, category=category, limit=limit)
    if not items:
        return f"No saved {category} items yet."
    lines = "\n".join(
        f"{index}. [{item.title}]({item.url})" for index, item in enumerate(items, start=1)
    )
    return f"**{heading}**\n\n{lines}"
