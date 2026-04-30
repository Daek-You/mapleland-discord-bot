from app.db.notice_repository import NoticeRecord, SqliteNoticeRepository


def test_sqlite_notice_repository_saves_notice_only_once(tmp_path) -> None:
    repository = SqliteNoticeRepository(str(tmp_path / "notices.sqlite3"))
    notice = NoticeRecord(
        title="New notice",
        url="https://maple.land/board/notices/100",
        external_id="100",
    )

    assert repository.save_notice_if_new(notice) is True
    assert repository.save_notice_if_new(notice) is False


def test_sqlite_notice_repository_reports_whether_notices_exist(tmp_path) -> None:
    repository = SqliteNoticeRepository(str(tmp_path / "notices.sqlite3"))

    assert repository.has_saved_notices() is False

    repository.save_notice_if_new(
        NoticeRecord(
            title="New notice",
            url="https://maple.land/board/notices/100",
            external_id="100",
        )
    )

    assert repository.has_saved_notices() is True


def test_sqlite_notice_repository_prevents_duplicate_external_id(tmp_path) -> None:
    repository = SqliteNoticeRepository(str(tmp_path / "notices.sqlite3"))

    assert repository.save_notice_if_new(
        NoticeRecord(
            title="Original notice",
            url="https://maple.land/board/notices/100",
            external_id="100",
        )
    )
    assert not repository.save_notice_if_new(
        NoticeRecord(
            title="Same external id",
            url="https://maple.land/board/notices/100-copy",
            external_id="100",
        )
    )
