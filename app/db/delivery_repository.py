"""SQLite persistence for reliable, idempotent Discord deliveries."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

from app.config import DEFAULT_NOTICE_DATABASE_PATH
from app.db.migration_runner import apply_migrations


class DeliveryStatus(str, Enum):
    """Lifecycle states for one revision delivery."""

    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"


@dataclass(frozen=True)
class DeliveryRecord:
    """A delivery lease claimed by the background sender."""

    id: int
    feed_revision_id: int
    channel_id: str
    attempt_count: int
    status: DeliveryStatus


class SqliteDeliveryRepository:
    """Queue deliveries with a lease so interrupted sends can be retried."""

    def __init__(self, database_path: str = DEFAULT_NOTICE_DATABASE_PATH) -> None:
        self.database_path = database_path
        apply_migrations(database_path)

    def enqueue(self, feed_revision_id: int, channel_id: str) -> bool:
        """Create one delivery per revision and channel, returning False for duplicates."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO deliveries (
                    feed_revision_id, channel_id, next_attempt_at
                )
                VALUES (?, ?, ?)
                """,
                (feed_revision_id, channel_id, _to_storage(datetime.now(UTC))),
            )
            connection.commit()
            return cursor.rowcount == 1

    def claim_ready(
        self,
        now: datetime,
        *,
        limit: int,
        lease_duration: timedelta,
    ) -> list[DeliveryRecord]:
        """Lease ready work atomically and reclaim work from expired leases."""
        if limit <= 0:
            raise ValueError("limit must be positive")
        if lease_duration <= timedelta():
            raise ValueError("lease_duration must be positive")

        now_value = _to_storage(now)
        lease_expires_at = _to_storage(now + lease_duration)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """
                SELECT id, feed_revision_id, channel_id, attempt_count
                FROM deliveries
                WHERE (status = ? AND next_attempt_at <= ?)
                   OR (status = ? AND lease_expires_at <= ?)
                ORDER BY next_attempt_at, id
                LIMIT ?
                """,
                (
                    DeliveryStatus.PENDING.value,
                    now_value,
                    DeliveryStatus.PROCESSING.value,
                    now_value,
                    limit,
                ),
            ).fetchall()
            delivery_ids = [row[0] for row in rows]
            for delivery_id in delivery_ids:
                connection.execute(
                    """
                    UPDATE deliveries
                    SET status = ?, attempt_count = attempt_count + 1,
                        lease_expires_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        DeliveryStatus.PROCESSING.value,
                        lease_expires_at,
                        now_value,
                        delivery_id,
                    ),
                )
            connection.commit()

        return [
            DeliveryRecord(
                id=row[0],
                feed_revision_id=row[1],
                channel_id=row[2],
                attempt_count=row[3] + 1,
                status=DeliveryStatus.PROCESSING,
            )
            for row in rows
        ]

    def reschedule(self, delivery_id: int, *, error_kind: str, retry_at: datetime) -> None:
        """Return a claimed delivery to the queue after an expected send failure."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE deliveries
                SET status = ?, next_attempt_at = ?, lease_expires_at = NULL,
                    last_error_kind = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    DeliveryStatus.PENDING.value,
                    _to_storage(retry_at),
                    error_kind,
                    _to_storage(datetime.now(UTC)),
                    delivery_id,
                    DeliveryStatus.PROCESSING.value,
                ),
            )
            connection.commit()
        if cursor.rowcount != 1:
            raise ValueError("delivery is not being processed")

    def mark_sent(
        self,
        delivery_id: int,
        *,
        discord_message_id: str,
        sent_at: datetime,
    ) -> None:
        """Finish a claimed delivery after Discord confirms the send."""
        sent_at_value = _to_storage(sent_at)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE deliveries
                SET status = ?, lease_expires_at = NULL, discord_message_id = ?,
                    sent_at = ?, updated_at = ?
                WHERE id = ? AND status = ?
                """,
                (
                    DeliveryStatus.SENT.value,
                    discord_message_id,
                    sent_at_value,
                    sent_at_value,
                    delivery_id,
                    DeliveryStatus.PROCESSING.value,
                ),
            )
            connection.commit()
        if cursor.rowcount != 1:
            raise ValueError("delivery is not being processed")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _to_storage(value: datetime) -> str:
    """Normalize queue timestamps to lexically sortable UTC text."""
    if value.tzinfo is None:
        raise ValueError("datetime must include a timezone")
    return value.astimezone(UTC).isoformat(timespec="microseconds")
