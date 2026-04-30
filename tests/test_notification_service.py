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

    notifications = collect_new_notice_notifications(
        fetch_notice_items=lambda: notice_items,
        notice_repository=repository,
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

    notifications = collect_new_notice_notifications(
        fetch_notice_items=lambda: notice_items,
        notice_repository=repository,
    )

    assert notifications == []
    assert [notice.external_id for notice in repository.saved_notices] == ["100", "101"]


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

    first_notifications = collect_new_notice_notifications(
        fetch_notice_items=lambda: notice_items,
        notice_repository=repository,
    )
    second_notifications = collect_new_notice_notifications(
        fetch_notice_items=lambda: notice_items,
        notice_repository=repository,
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

    collect_new_notice_notifications(
        fetch_notice_items=lambda: [
            NoticeItem(
                title="Original notice",
                url="https://maple.land/board/notices/100",
            )
        ],
        notice_repository=repository,
    )
    notifications = collect_new_notice_notifications(
        fetch_notice_items=lambda: [
            NoticeItem(
                title="Same external id",
                url="https://maple.land/board/notices/100/",
            )
        ],
        notice_repository=repository,
    )

    assert notifications == []


def test_collect_test_notice_notifications_uses_fake_notice_data() -> None:
    repository = FakeNoticeRepository()

    notifications = collect_test_notice_notifications(
        "test-run",
        notice_repository=repository,
    )

    assert len(notifications) == 1
    assert notifications[0].title == TEST_NOTICE_TITLE
    assert notifications[0].url == f"{TEST_NOTICE_URL}/test-run"


def test_format_notice_notification_returns_title_and_url() -> None:
    message = format_notice_notification(
        collect_test_notice_notifications(
            "message-format",
            notice_repository=FakeNoticeRepository(),
        )[0]
    )

    assert message == f"{TEST_NOTICE_TITLE}\n{TEST_NOTICE_URL}/message-format"


def test_collect_new_notice_notifications_returns_empty_on_crawler_error() -> None:
    def raise_crawler_error() -> list[NoticeItem]:
        raise MaplelandCrawlerError("failed")

    notifications = collect_new_notice_notifications(
        fetch_notice_items=raise_crawler_error,
        notice_repository=FakeNoticeRepository(),
    )

    assert notifications == []
