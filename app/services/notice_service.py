"""Service logic for Mapleland notices."""

import logging
from collections.abc import Callable

from app.crawler.mapleland import MaplelandCrawlerError, NoticeItem, fetch_latest_notice_items


NOTICE_COMMAND_EMPTY_MESSAGE = "현재 가져올 수 있는 공지가 없습니다."
NOTICE_COMMAND_FAILURE_MESSAGE = "공지사항을 가져오는 데 실패했습니다. 잠시 후 다시 시도해주세요."
DEFAULT_NOTICE_DISPLAY_LIMIT = 5

logger = logging.getLogger(__name__)


def get_latest_notice_message(
    fetch_notice_items: Callable[[], list[NoticeItem]] = fetch_latest_notice_items,
    display_limit: int = DEFAULT_NOTICE_DISPLAY_LIMIT,
) -> str:
    """Return a Discord-ready latest notices message."""
    try:
        notice_items = fetch_notice_items()
    except MaplelandCrawlerError:
        logger.exception("Failed to fetch Mapleland notices.")
        return NOTICE_COMMAND_FAILURE_MESSAGE

    return format_notice_items(notice_items[:display_limit])


def format_notice_items(notice_items: list[NoticeItem]) -> str:
    """Format notice items as a numbered Discord message."""
    if not notice_items:
        return NOTICE_COMMAND_EMPTY_MESSAGE

    return "\n".join(
        f"{index}. {notice_item.title}\n{notice_item.url}"
        for index, notice_item in enumerate(notice_items, start=1)
    )
