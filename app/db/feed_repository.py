"""SQLite persistence for normalized feed items and their revisions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum

from app.config import DEFAULT_NOTICE_DATABASE_PATH
from app.db.migration_runner import apply_migrations


class FeedChange(str, Enum):
    """Result of comparing a collected item with stored state."""

    NEW = "new"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class FeedItemRecord:
    """Normalized content collected from one external source."""

    source: str
    category: str
    external_id: str
    url: str
    title: str
    content_hash: str
    content: str
    published_at: str | None = None
    source_updated_at: str | None = None
    status: str = "active"


@dataclass(frozen=True)
class FeedSaveResult:
    """Stored item identity and detected change type."""

    item_id: int
    change: FeedChange
    revision_id: int | None


class SqliteFeedRepository:
    """Store feed items and append a revision whenever their content changes."""

    def __init__(self, database_path: str = DEFAULT_NOTICE_DATABASE_PATH) -> None:
        self.database_path = database_path
        apply_migrations(database_path)

    def save(self, item: FeedItemRecord) -> FeedSaveResult:
        """Insert or update an item and return the detected change."""
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT id, current_content_hash
                FROM feed_items
                WHERE source = ? AND external_id = ?
                """,
                (item.source, item.external_id),
            ).fetchone()

            if existing is None:
                item_id = self._insert_item(connection, item)
                revision_id = self._insert_revision(connection, item_id, item)
                connection.commit()
                return FeedSaveResult(
                    item_id=item_id,
                    change=FeedChange.NEW,
                    revision_id=revision_id,
                )

            item_id, stored_hash = existing
            if stored_hash == item.content_hash:
                self._refresh_unchanged_item(connection, item_id, item)
                connection.commit()
                return FeedSaveResult(
                    item_id=item_id,
                    change=FeedChange.UNCHANGED,
                    revision_id=None,
                )

            self._update_changed_item(connection, item_id, item)
            revision_id = self._insert_revision(connection, item_id, item)
            connection.commit()
            return FeedSaveResult(
                item_id=item_id,
                change=FeedChange.UPDATED,
                revision_id=revision_id,
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _insert_item(connection: sqlite3.Connection, item: FeedItemRecord) -> int:
        cursor = connection.execute(
            """
            INSERT INTO feed_items (
                source, category, external_id, url, title,
                published_at, source_updated_at, current_content_hash, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.source,
                item.category,
                item.external_id,
                item.url,
                item.title,
                item.published_at,
                item.source_updated_at,
                item.content_hash,
                item.status,
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _insert_revision(
        connection: sqlite3.Connection,
        item_id: int,
        item: FeedItemRecord,
    ) -> int:
        cursor = connection.execute(
            """
            INSERT INTO feed_revisions (feed_item_id, content_hash, content)
            VALUES (?, ?, ?)
            """,
            (item_id, item.content_hash, item.content),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _refresh_unchanged_item(
        connection: sqlite3.Connection,
        item_id: int,
        item: FeedItemRecord,
    ) -> None:
        connection.execute(
            """
            UPDATE feed_items
            SET title = ?, url = ?, published_at = ?, source_updated_at = ?,
                last_checked_at = CURRENT_TIMESTAMP, status = ?
            WHERE id = ?
            """,
            (
                item.title,
                item.url,
                item.published_at,
                item.source_updated_at,
                item.status,
                item_id,
            ),
        )

    @staticmethod
    def _update_changed_item(
        connection: sqlite3.Connection,
        item_id: int,
        item: FeedItemRecord,
    ) -> None:
        connection.execute(
            """
            UPDATE feed_items
            SET category = ?, url = ?, title = ?, published_at = ?,
                source_updated_at = ?, current_content_hash = ?,
                last_checked_at = CURRENT_TIMESTAMP, status = ?
            WHERE id = ?
            """,
            (
                item.category,
                item.url,
                item.title,
                item.published_at,
                item.source_updated_at,
                item.content_hash,
                item.status,
                item_id,
            ),
        )
