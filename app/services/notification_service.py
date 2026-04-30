"""Service logic for Mapleland notice notifications."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from app.crawler.mapleland import MaplelandCrawlerError, NoticeItem, fetch_latest_notice_items
from app.db.notice_repository import NoticeRecord, create_default_notice_repository


logger = logging.getLogger(__name__)

NOTICE_SOURCE = "mapleland"
TEST_NOTICE_TITLE = "TEST NOTICE"
TEST_NOTICE_URL = "https://maple.land/board/notices/test-notification"


class NoticeRepository(Protocol):
    """Persistence contract needed for duplicate notice detection."""

    def save_notice_if_new(self, notice: NoticeRecord) -> bool:
        """Persist a notice and return True when it is newly inserted."""

    def has_saved_notices(self) -> bool:
        """Return whether any notice has already been stored."""


@dataclass(frozen=True)
class NoticeNotification:
    """Discord-ready notification content."""

    title: str
    url: str


def collect_new_notice_notifications(
    fetch_notice_items: Callable[[], list[NoticeItem]] = fetch_latest_notice_items,
    notice_repository: NoticeRepository | None = None,
    suppress_initial_notifications: bool = True,
) -> list[NoticeNotification]:
    """Return notifications for notices that have not been stored yet."""
    repository = notice_repository or create_default_notice_repository()

    try:
        notice_items = fetch_notice_items()
    except MaplelandCrawlerError:
        logger.exception("Failed to fetch Mapleland notices for notification.")
        return []

    should_notify = not suppress_initial_notifications or repository.has_saved_notices()
    notifications: list[NoticeNotification] = []
    for notice_item in notice_items:
        notice_record = NoticeRecord(
            title=notice_item.title,
            url=notice_item.url,
            external_id=_get_notice_external_id(notice_item.url),
            source=NOTICE_SOURCE,
        )
        if repository.save_notice_if_new(notice_record) and should_notify:
            notifications.append(
                NoticeNotification(title=notice_item.title, url=notice_item.url)
            )

    return notifications


def collect_test_notice_notifications(
    unique_suffix: str,
    notice_repository: NoticeRepository | None = None,
) -> list[NoticeNotification]:
    """Create a fake notice notification through the real duplicate check path."""
    fake_notice = NoticeItem(
        title=TEST_NOTICE_TITLE,
        url=f"{TEST_NOTICE_URL}/{unique_suffix}",
    )
    return collect_new_notice_notifications(
        fetch_notice_items=lambda: [fake_notice],
        notice_repository=notice_repository,
        suppress_initial_notifications=False,
    )


def format_notice_notification(notification: NoticeNotification) -> str:
    """Format a single notice notification for Discord."""
    return f"{notification.title}\n{notification.url}"


def _get_notice_external_id(url: str) -> str:
    parsed_url = urlparse(url)
    notice_id = parsed_url.path.rstrip("/").split("/")[-1]
    return notice_id or url
