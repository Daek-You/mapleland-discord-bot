"""SQLite persistence for channels subscribed to feed categories."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from app.config import DEFAULT_NOTICE_DATABASE_PATH
from app.db.migration_runner import apply_migrations


@dataclass(frozen=True)
class FeedSubscription:
    """One channel and optional role to notify for a feed category."""

    id: int
    category: str
    channel_id: str
    role_id: str | None


class SqliteSubscriptionRepository:
    """Create, update, disable, and query category subscriptions."""

    def __init__(self, database_path: str = DEFAULT_NOTICE_DATABASE_PATH) -> None:
        self.database_path = database_path
        apply_migrations(database_path)

    def save(self, *, category: str, channel_id: str, role_id: str | None = None) -> None:
        """Enable a category subscription, replacing its optional role setting."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feed_subscriptions (category, channel_id, role_id)
                VALUES (?, ?, ?)
                ON CONFLICT(category, channel_id) DO UPDATE SET
                    role_id = excluded.role_id,
                    enabled = 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (category, channel_id, role_id),
            )
            connection.commit()

    def disable(self, *, category: str, channel_id: str) -> bool:
        """Disable one subscription without deleting its configuration history."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE feed_subscriptions
                SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                WHERE category = ? AND channel_id = ? AND enabled = 1
                """,
                (category, channel_id),
            )
            connection.commit()
            return cursor.rowcount == 1

    def list_enabled(self, *, category: str) -> list[FeedSubscription]:
        """Return active subscriptions for exactly one feed category."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, category, channel_id, role_id
                FROM feed_subscriptions
                WHERE category = ? AND enabled = 1
                ORDER BY id
                """,
                (category,),
            ).fetchall()
        return [FeedSubscription(*row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)


def create_default_subscription_repository() -> SqliteSubscriptionRepository:
    """Create the configured feed subscription repository."""
    return SqliteSubscriptionRepository()
