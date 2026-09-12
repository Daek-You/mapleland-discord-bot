"""Persistence helpers for Mapleland notices."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.config import DEFAULT_NOTICE_DATABASE_PATH, get_notice_database_path
from app.db.migration_runner import apply_migrations


@dataclass(frozen=True)
class NoticeRecord:
    """Notice data stored for duplicate detection."""

    title: str
    url: str
    external_id: str
    source: str = "mapleland"


class SqliteNoticeRepository:
    """SQLite-backed notice repository."""

    def __init__(self, database_path: str = DEFAULT_NOTICE_DATABASE_PATH) -> None:
        self.database_path = database_path
        self._ensure_database()

    def save_notice_if_new(self, notice: NoticeRecord) -> bool:
        """Save a notice and return True only when it did not exist before."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO notices (source, external_id, title, url)
                VALUES (?, ?, ?, ?)
                """,
                (notice.source, notice.external_id, notice.title, notice.url),
            )
            connection.commit()
            return cursor.rowcount == 1

    def has_saved_notices(self) -> bool:
        """Return whether any notice has already been stored."""
        with self._connect() as connection:
            cursor = connection.execute("SELECT 1 FROM notices LIMIT 1")
            return cursor.fetchone() is not None

    def _ensure_database(self) -> None:
        apply_migrations(self.database_path)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)


def create_default_notice_repository() -> SqliteNoticeRepository:
    """Create the configured notice repository."""
    return SqliteNoticeRepository(get_notice_database_path())
