import sqlite3

import pytest

from app.db.feed_repository import FeedChange, FeedItemRecord, SqliteFeedRepository


def make_feed_item(
    *,
    title: str = "첫 공지",
    content_hash: str = "hash-v1",
    content: str = "첫 공지 본문",
) -> FeedItemRecord:
    return FeedItemRecord(
        source="mapleland",
        category="notice",
        external_id="100",
        url="https://maple.land/board/notices/100",
        title=title,
        content_hash=content_hash,
        content=content,
        published_at="2026-09-12T10:00:00+09:00",
    )


def test_save_new_feed_item_creates_first_revision(tmp_path) -> None:
    database_path = tmp_path / "feed.sqlite3"
    repository = SqliteFeedRepository(str(database_path))

    result = repository.save(make_feed_item())

    assert result.change is FeedChange.NEW
    with sqlite3.connect(database_path) as connection:
        item = connection.execute(
            "SELECT source, category, title, current_content_hash FROM feed_items"
        ).fetchone()
        revisions = connection.execute(
            "SELECT content_hash, content FROM feed_revisions"
        ).fetchall()
    assert item == ("mapleland", "notice", "첫 공지", "hash-v1")
    assert revisions == [("hash-v1", "첫 공지 본문")]


def test_save_same_content_is_unchanged_without_extra_revision(tmp_path) -> None:
    database_path = tmp_path / "feed.sqlite3"
    repository = SqliteFeedRepository(str(database_path))
    first_result = repository.save(make_feed_item())

    second_result = repository.save(make_feed_item(title="표시 제목 보정"))

    assert second_result == type(first_result)(
        item_id=first_result.item_id,
        change=FeedChange.UNCHANGED,
        revision_id=None,
    )
    with sqlite3.connect(database_path) as connection:
        title = connection.execute("SELECT title FROM feed_items").fetchone()[0]
        revision_count = connection.execute(
            "SELECT COUNT(*) FROM feed_revisions"
        ).fetchone()[0]
    assert title == "표시 제목 보정"
    assert revision_count == 1


def test_save_changed_content_updates_item_and_appends_revision(tmp_path) -> None:
    database_path = tmp_path / "feed.sqlite3"
    repository = SqliteFeedRepository(str(database_path))
    first_result = repository.save(make_feed_item())

    second_result = repository.save(
        make_feed_item(
            title="수정된 공지",
            content_hash="hash-v2",
            content="수정된 공지 본문",
        )
    )

    assert second_result.item_id == first_result.item_id
    assert second_result.change is FeedChange.UPDATED
    with sqlite3.connect(database_path) as connection:
        current = connection.execute(
            "SELECT title, current_content_hash FROM feed_items"
        ).fetchone()
        revisions = connection.execute(
            "SELECT content_hash FROM feed_revisions ORDER BY id"
        ).fetchall()
    assert current == ("수정된 공지", "hash-v2")
    assert revisions == [("hash-v1",), ("hash-v2",)]


def test_feed_revision_foreign_key_is_enforced(tmp_path) -> None:
    database_path = tmp_path / "feed.sqlite3"
    repository = SqliteFeedRepository(str(database_path))

    with repository._connect() as connection:
        foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO feed_revisions (feed_item_id, content_hash, content)
                VALUES (999, 'missing', 'missing item')
                """
            )

    assert foreign_keys_enabled == 1
