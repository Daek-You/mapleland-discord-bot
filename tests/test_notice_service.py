import logging

from app.crawler.mapleland import MaplelandCrawlerError, NoticeItem
from app.services.notice_service import (
    NOTICE_COMMAND_EMPTY_MESSAGE,
    NOTICE_COMMAND_FAILURE_MESSAGE,
    NOTICE_COMMAND_HEADER,
    format_notice_items,
    get_latest_notice_message,
)


def test_format_notice_items_returns_markdown_notice_list() -> None:
    notice_items = [
        NoticeItem(title="첫 번째 공지", url="https://maple.land/board/notices/first"),
        NoticeItem(title="두 번째 공지", url="https://maple.land/board/notices/second"),
    ]

    assert format_notice_items(notice_items) == (
        f"{NOTICE_COMMAND_HEADER}\n\n"
        "1. [첫 번째 공지](https://maple.land/board/notices/first)\n"
        "2. [두 번째 공지](https://maple.land/board/notices/second)"
    )


def test_format_notice_items_escapes_markdown_link_text() -> None:
    notice_items = [
        NoticeItem(title="[긴급] 공지", url="https://maple.land/board/notices/urgent"),
    ]

    assert "\\[긴급\\] 공지" in format_notice_items(notice_items)


def test_format_notice_items_returns_empty_message() -> None:
    assert format_notice_items([]) == NOTICE_COMMAND_EMPTY_MESSAGE


def test_get_latest_notice_message_limits_notices_to_five() -> None:
    notice_items = [
        NoticeItem(title=f"공지 {index}", url=f"https://maple.land/board/notices/{index}")
        for index in range(1, 7)
    ]

    message = get_latest_notice_message(lambda: notice_items)

    assert "5. [공지 5](https://maple.land/board/notices/5)" in message
    assert "공지 6" not in message


def test_get_latest_notice_message_returns_failure_message_and_logs_exception(
    caplog,
) -> None:
    def raise_crawler_error() -> list[NoticeItem]:
        raise MaplelandCrawlerError("crawler failed")

    with caplog.at_level(logging.ERROR):
        message = get_latest_notice_message(raise_crawler_error)

    assert message == NOTICE_COMMAND_FAILURE_MESSAGE
    assert "Failed to fetch Mapleland notices." in caplog.text
