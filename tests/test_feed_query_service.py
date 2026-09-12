import asyncio

from app.db.feed_repository import FeedSummary
from app.services.feed_query_service import get_latest_feed_message


class FakeFeedRepository:
    def __init__(self, items: list[FeedSummary]) -> None:
        self.items = items

    def list_latest(self, *, category: str, limit: int) -> list[FeedSummary]:
        assert category == "event"
        assert limit == 5
        return self.items


def test_get_latest_feed_message_formats_markdown_links() -> None:
    message = asyncio.run(
        get_latest_feed_message(
            FakeFeedRepository([FeedSummary(category="event", title="Event", url="https://example.com")]),
            category="event",
            heading="Latest events",
        )
    )

    assert message == "**Latest events**\n\n1. [Event](https://example.com)"


def test_get_latest_feed_message_handles_empty_category() -> None:
    message = asyncio.run(
        get_latest_feed_message(FakeFeedRepository([]), category="event", heading="Latest events")
    )

    assert message == "No saved event items yet."
