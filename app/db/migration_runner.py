"""Ordered SQLite schema migrations and pre-migration backups."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_MIGRATIONS_DIRECTORY = Path(__file__).with_name("migrations")
MIGRATION_FILE_PATTERN = re.compile(r"^(?P<version>\d{3})_(?P<name>[a-z0-9_]+)\.sql$")


@dataclass(frozen=True)
class Migration:
    """One numbered SQL migration file."""

    version: int
    name: str
    path: Path


def apply_migrations(
    database_path: str | Path,
    migrations_directory: str | Path = DEFAULT_MIGRATIONS_DIRECTORY,
    backup_directory: str | Path | None = None,
) -> list[int]:
    """Back up an existing database and apply every pending migration."""
    database_file = Path(database_path)
    _ensure_parent_directory(database_file)
    migrations = discover_migrations(migrations_directory)
    applied_versions = _read_applied_versions(database_file)
    pending_migrations = [
        migration for migration in migrations if migration.version not in applied_versions
    ]
    if not pending_migrations:
        return []

    if database_file.exists() and database_file.stat().st_size > 0:
        create_database_backup(database_file, backup_directory=backup_directory)

    with sqlite3.connect(database_file) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _create_schema_migrations_table(connection)
        for migration in pending_migrations:
            _apply_migration(connection, migration)

    return [migration.version for migration in pending_migrations]


def discover_migrations(
    migrations_directory: str | Path = DEFAULT_MIGRATIONS_DIRECTORY,
) -> list[Migration]:
    """Return valid migration files in version order."""
    directory = Path(migrations_directory)
    if not directory.is_dir():
        raise RuntimeError(f"Migration directory does not exist: {directory}")
    migrations: list[Migration] = []
    for path in sorted(directory.glob("*.sql")):
        match = MIGRATION_FILE_PATTERN.fullmatch(path.name)
        if match is None:
            raise RuntimeError(f"Invalid migration filename: {path.name}")
        migrations.append(
            Migration(
                version=int(match.group("version")),
                name=match.group("name"),
                path=path,
            )
        )

    versions = [migration.version for migration in migrations]
    if len(versions) != len(set(versions)):
        raise RuntimeError("Migration versions must be unique.")
    return migrations


def create_database_backup(
    database_path: str | Path,
    backup_directory: str | Path | None = None,
) -> Path:
    """Create a consistent SQLite backup and return its path."""
    database_file = Path(database_path)
    if not database_file.exists():
        raise FileNotFoundError(database_file)

    target_directory = (
        Path(backup_directory) if backup_directory else database_file.parent / "backups"
    )
    target_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup_file = target_directory / f"{database_file.stem}-{timestamp}.sqlite3"

    with sqlite3.connect(database_file) as source_connection:
        with sqlite3.connect(backup_file) as backup_connection:
            source_connection.backup(backup_connection)
    return backup_file


def _read_applied_versions(database_file: Path) -> set[int]:
    if not database_file.exists() or database_file.stat().st_size == 0:
        return set()
    with sqlite3.connect(database_file) as connection:
        table_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_migrations'
            """
        ).fetchone()
        if table_exists is None:
            return set()
        return {
            row[0]
            for row in connection.execute("SELECT version FROM schema_migrations")
        }


def _create_schema_migrations_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()


def _apply_migration(connection: sqlite3.Connection, migration: Migration) -> None:
    migration_name = migration.name.replace("'", "''")
    script = migration.path.read_text(encoding="utf-8")
    try:
        connection.executescript(
            "BEGIN IMMEDIATE;\n"
            f"{script}\n"
            "INSERT INTO schema_migrations (version, name) "
            f"VALUES ({migration.version}, '{migration_name}');\n"
            "COMMIT;"
        )
    except sqlite3.Error:
        connection.rollback()
        raise


def _ensure_parent_directory(database_file: Path) -> None:
    if database_file.parent != Path("."):
        database_file.parent.mkdir(parents=True, exist_ok=True)
