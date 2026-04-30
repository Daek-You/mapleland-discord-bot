"""Persistence helpers for Mapleland notices."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.config import DEFAULT_NOTICE_DATABASE_PATH, get_notice_database_path


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
        database_file = Path(self.database_path)
        if database_file.parent != Path("."):
            database_file.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS notices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)


def create_default_notice_repository() -> SqliteNoticeRepository:
    """Create the configured notice repository."""
    return SqliteNoticeRepository(get_notice_database_path())
