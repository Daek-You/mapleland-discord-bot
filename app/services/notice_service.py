"""Service logic for Mapleland notices."""

import logging
from collections.abc import Awaitable, Callable

from app.config import DEFAULT_NOTICE_DISPLAY_LIMIT
from app.crawler.mapleland import MaplelandCrawlerError, NoticeItem, fetch_latest_notice_items

NOTICE_COMMAND_EMPTY_MESSAGE = "현재 가져올 수 있는 공지가 없습니다."
NOTICE_COMMAND_FAILURE_MESSAGE = "공지사항을 가져오는 데 실패했습니다. 잠시 후 다시 시도해주세요."
NOTICE_COMMAND_HEADER = "**📢 최신 메이플랜드 공지**"
MARKDOWN_LINK_TEXT_SPECIAL_CHARACTERS = "\\[]"

logger = logging.getLogger(__name__)


async def get_latest_notice_message(
    fetch_notice_items: Callable[[], Awaitable[list[NoticeItem]]] = fetch_latest_notice_items,
    display_limit: int = DEFAULT_NOTICE_DISPLAY_LIMIT,
) -> str:
    """Return a Discord-ready latest notices message."""
    try:
        notice_items = await fetch_notice_items()
    except MaplelandCrawlerError:
        logger.error("Failed to fetch Mapleland notices.", exc_info=True)
        return NOTICE_COMMAND_FAILURE_MESSAGE

    return format_notice_items(notice_items[:display_limit])


def format_notice_items(notice_items: list[NoticeItem]) -> str:
    """Format notice items as a Markdown numbered Discord message."""
    if not notice_items:
        return NOTICE_COMMAND_EMPTY_MESSAGE

    notice_lines = "\n".join(
        f"{index}. [{_escape_markdown_link_text(notice_item.title)}]({notice_item.url})"
        for index, notice_item in enumerate(notice_items, start=1)
    )
    return f"{NOTICE_COMMAND_HEADER}\n\n{notice_lines}"


def _escape_markdown_link_text(text: str) -> str:
    return "".join(
        f"\\{character}" if character in MARKDOWN_LINK_TEXT_SPECIAL_CHARACTERS else character
        for character in text
    )
