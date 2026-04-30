from app.config import (
    DEFAULT_NOTICE_CHECK_INTERVAL_SECONDS,
    DEFAULT_NOTICE_DATABASE_PATH,
    NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME,
    NOTICE_DATABASE_PATH_ENV_NAME,
    get_notice_check_interval_seconds,
    get_notice_database_path,
)


TEST_NOTICE_CHECK_INTERVAL_SECONDS = 30


def test_get_notice_check_interval_seconds_returns_default(monkeypatch) -> None:
    monkeypatch.delenv(NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME, raising=False)

    assert get_notice_check_interval_seconds() == DEFAULT_NOTICE_CHECK_INTERVAL_SECONDS


def test_get_notice_check_interval_seconds_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        NOTICE_CHECK_INTERVAL_SECONDS_ENV_NAME,
        str(TEST_NOTICE_CHECK_INTERVAL_SECONDS),
    )

    assert get_notice_check_interval_seconds() == TEST_NOTICE_CHECK_INTERVAL_SECONDS


def test_get_notice_database_path_returns_default_for_empty_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(NOTICE_DATABASE_PATH_ENV_NAME, "")

    assert get_notice_database_path() == DEFAULT_NOTICE_DATABASE_PATH
