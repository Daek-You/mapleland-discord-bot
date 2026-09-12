import sqlite3

import pytest

from app.db.migration_runner import apply_migrations, create_database_backup


def test_apply_migrations_creates_schema_and_records_version(tmp_path) -> None:
    database_path = tmp_path / "notices.sqlite3"

    applied_versions = apply_migrations(database_path)

    assert applied_versions == [1, 2, 3, 4]
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        versions = connection.execute(
            "SELECT version, name FROM schema_migrations"
        ).fetchall()
    assert "notices" in tables
    assert "feed_items" in tables
    assert "feed_revisions" in tables
    assert "deliveries" in tables
    assert "feed_subscriptions" in tables
    assert versions == [
        (1, "create_notices"),
        (2, "create_feed_tables"),
        (3, "create_deliveries"),
        (4, "create_feed_subscriptions"),
    ]


def test_apply_migrations_is_idempotent_and_does_not_create_extra_backup(tmp_path) -> None:
    database_path = tmp_path / "notices.sqlite3"
    backup_directory = tmp_path / "backups"

    assert apply_migrations(database_path, backup_directory=backup_directory) == [1, 2, 3, 4]
    assert apply_migrations(database_path, backup_directory=backup_directory) == []

    assert list(backup_directory.glob("*.sqlite3")) == []


def test_apply_migrations_backs_up_legacy_database_before_schema_change(tmp_path) -> None:
    database_path = tmp_path / "notices.sqlite3"
    backup_directory = tmp_path / "backups"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE legacy_data (value TEXT NOT NULL)")
        connection.execute("INSERT INTO legacy_data (value) VALUES ('keep-me')")
        connection.commit()

    assert apply_migrations(database_path, backup_directory=backup_directory) == [1, 2, 3, 4]

    backup_files = list(backup_directory.glob("*.sqlite3"))
    assert len(backup_files) == 1
    with sqlite3.connect(backup_files[0]) as connection:
        assert connection.execute("SELECT value FROM legacy_data").fetchone() == (
            "keep-me",
        )
        schema_table = connection.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'schema_migrations'
            """
        ).fetchone()
    assert schema_table is None


def test_failed_migration_rolls_back_and_does_not_record_version(tmp_path) -> None:
    database_path = tmp_path / "notices.sqlite3"
    migrations_directory = tmp_path / "migrations"
    migrations_directory.mkdir()
    (migrations_directory / "001_create_example.sql").write_text(
        "CREATE TABLE example (id INTEGER PRIMARY KEY);",
        encoding="utf-8",
    )
    (migrations_directory / "002_invalid_statement.sql").write_text(
        "CREATE TABLE broken (",
        encoding="utf-8",
    )

    with pytest.raises(sqlite3.Error):
        apply_migrations(database_path, migrations_directory=migrations_directory)

    with sqlite3.connect(database_path) as connection:
        versions = connection.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        broken_table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'broken'"
        ).fetchone()
    assert versions == [(1,)]
    assert broken_table is None


def test_create_database_backup_copies_committed_data(tmp_path) -> None:
    database_path = tmp_path / "source.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE example (value TEXT NOT NULL)")
        connection.execute("INSERT INTO example (value) VALUES ('saved')")
        connection.commit()

    backup_path = create_database_backup(
        database_path,
        backup_directory=tmp_path / "backups",
    )

    with sqlite3.connect(backup_path) as connection:
        assert connection.execute("SELECT value FROM example").fetchone() == (
            "saved",
        )
