import asyncio
import threading

from app.crawler.mapleland import MaplelandCrawlerError, NoticeItem
from app.db.notice_repository import NoticeRecord
from app.services.notification_service import (
    TEST_NOTICE_TITLE,
    TEST_NOTICE_URL,
    collect_new_notice_notifications,
    collect_test_notice_notifications,
    format_notice_notification,
)


class FakeNoticeRepository:
    def __init__(self) -> None:
        self.external_ids: set[str] = set()
        self.urls: set[str] = set()
        self.saved_notices: list[NoticeRecord] = []

    def save_notice_if_new(self, notice: NoticeRecord) -> bool:
        if notice.external_id in self.external_ids or notice.url in self.urls:
            return False

        self.external_ids.add(notice.external_id)
        self.urls.add(notice.url)
        self.saved_notices.append(notice)
        return True

    def has_saved_notices(self) -> bool:
        return bool(self.saved_notices)


async def return_notice_items(notice_items: list[NoticeItem]) -> list[NoticeItem]:
    return notice_items


def test_collect_new_notice_notifications_detects_new_notices() -> None:
    repository = FakeNoticeRepository()
    repository.save_notice_if_new(
        NoticeRecord(
            title="Existing notice",
            url="https://maple.land/board/notices/99",
            external_id="99",
        )
    )
    notice_items = [
        NoticeItem(
            title="New notice",
            url="https://maple.land/board/notices/100",
        )
    ]

    notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(notice_items),
            notice_repository=repository,
        )
    )

    assert len(notifications) == 1
    assert notifications[0].title == "New notice"
    assert notifications[0].url == "https://maple.land/board/notices/100"
    assert repository.saved_notices[-1].external_id == "100"


def test_collect_new_notice_notifications_initializes_empty_repository_without_notifications() -> None:
    repository = FakeNoticeRepository()
    notice_items = [
        NoticeItem(
            title="Existing notice one",
            url="https://maple.land/board/notices/100",
        ),
        NoticeItem(
            title="Existing notice two",
            url="https://maple.land/board/notices/101",
        ),
    ]

    notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(notice_items),
            notice_repository=repository,
        )
    )

    assert notifications == []
    assert [notice.external_id for notice in repository.saved_notices] == ["100", "101"]


def test_collect_notice_notifications_suppresses_backlog_on_runtime_start() -> None:
    repository = FakeNoticeRepository()
    repository.save_notice_if_new(
        NoticeRecord(
            title="Old stored notice",
            url="https://maple.land/board/notices/99",
            external_id="99",
        )
    )

    notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(
                [NoticeItem(title="Backlog", url="https://maple.land/board/notices/100")]
            ),
            notice_repository=repository,
            suppress_current_notifications=True,
        )
    )

    assert notifications == []


def test_collect_notice_notifications_returns_oldest_first_for_chat_order() -> None:
    repository = FakeNoticeRepository()
    repository.save_notice_if_new(
        NoticeRecord(
            title="Stored notice",
            url="https://maple.land/board/notices/99",
            external_id="99",
        )
    )
    newest_first_items = [
        NoticeItem(title="Newest", url="https://maple.land/board/notices/102"),
        NoticeItem(title="Older", url="https://maple.land/board/notices/101"),
    ]

    notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(newest_first_items),
            notice_repository=repository,
        )
    )

    assert [notification.title for notification in notifications] == ["Older", "Newest"]


def test_collect_new_notice_notifications_prevents_duplicate_by_url() -> None:
    repository = FakeNoticeRepository()
    repository.save_notice_if_new(
        NoticeRecord(
            title="Existing notice",
            url="https://maple.land/board/notices/99",
            external_id="99",
        )
    )
    notice_items = [
        NoticeItem(
            title="New notice",
            url="https://maple.land/board/notices/100",
        )
    ]

    first_notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(notice_items),
            notice_repository=repository,
        )
    )
    second_notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(notice_items),
            notice_repository=repository,
        )
    )

    assert len(first_notifications) == 1
    assert second_notifications == []


def test_collect_new_notice_notifications_prevents_duplicate_by_external_id() -> None:
    repository = FakeNoticeRepository()
    repository.save_notice_if_new(
        NoticeRecord(
            title="Existing notice",
            url="https://maple.land/board/notices/99",
            external_id="99",
        )
    )

    asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(
                [
                    NoticeItem(
                        title="Original notice",
                        url="https://maple.land/board/notices/100",
                    )
                ]
            ),
            notice_repository=repository,
        )
    )
    notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(
                [
                    NoticeItem(
                        title="Same external id",
                        url="https://maple.land/board/notices/100/",
                    )
                ]
            ),
            notice_repository=repository,
        )
    )

    assert notifications == []


def test_collect_test_notice_notifications_uses_fake_notice_data() -> None:
    repository = FakeNoticeRepository()

    notifications = asyncio.run(
        collect_test_notice_notifications(
            "test-run",
            notice_repository=repository,
        )
    )

    assert len(notifications) == 1
    assert notifications[0].title == TEST_NOTICE_TITLE
    assert notifications[0].url == f"{TEST_NOTICE_URL}/test-run"


def test_format_notice_notification_returns_title_and_url() -> None:
    notification = asyncio.run(
        collect_test_notice_notifications(
            "message-format",
            notice_repository=FakeNoticeRepository(),
        )
    )
    message = format_notice_notification(notification[0])

    assert message == f"{TEST_NOTICE_TITLE}\n{TEST_NOTICE_URL}/message-format"


def test_collect_new_notice_notifications_returns_empty_on_crawler_error() -> None:
    async def raise_crawler_error() -> list[NoticeItem]:
        raise MaplelandCrawlerError("failed")

    notifications = asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=raise_crawler_error,
            notice_repository=FakeNoticeRepository(),
        )
    )

    assert notifications == []


def test_collect_new_notice_notifications_runs_repository_calls_in_worker_thread() -> None:
    event_loop_thread_id = threading.get_ident()

    class ThreadRecordingRepository(FakeNoticeRepository):
        def __init__(self) -> None:
            super().__init__()
            self.thread_ids: list[int] = []

        def has_saved_notices(self) -> bool:
            self.thread_ids.append(threading.get_ident())
            return super().has_saved_notices()

        def save_notice_if_new(self, notice: NoticeRecord) -> bool:
            self.thread_ids.append(threading.get_ident())
            return super().save_notice_if_new(notice)

    repository = ThreadRecordingRepository()
    notice_items = [
        NoticeItem(
            title="New notice",
            url="https://maple.land/board/notices/100",
        )
    ]

    asyncio.run(
        collect_new_notice_notifications(
            fetch_notice_items=lambda: return_notice_items(notice_items),
            notice_repository=repository,
        )
    )

    assert repository.thread_ids
    assert all(thread_id != event_loop_thread_id for thread_id in repository.thread_ids)
