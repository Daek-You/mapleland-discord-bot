import sqlite3

from app.db.subscription_repository import SqliteSubscriptionRepository


def test_save_creates_and_lists_enabled_subscription(tmp_path) -> None:
    repository = SqliteSubscriptionRepository(str(tmp_path / "subscriptions.sqlite3"))

    repository.save(category="notice", channel_id="123", role_id="456")

    subscriptions = repository.list_enabled(category="notice")
    assert len(subscriptions) == 1
    subscription = subscriptions[0]
    assert (subscription.category, subscription.channel_id, subscription.role_id) == (
        "notice",
        "123",
        "456",
    )


def test_save_updates_role_and_reenables_disabled_subscription(tmp_path) -> None:
    repository = SqliteSubscriptionRepository(str(tmp_path / "subscriptions.sqlite3"))
    repository.save(category="notice", channel_id="123", role_id="456")
    assert repository.disable(category="notice", channel_id="123") is True

    repository.save(category="notice", channel_id="123", role_id=None)

    subscriptions = repository.list_enabled(category="notice")
    assert len(subscriptions) == 1
    assert subscriptions[0].role_id is None


def test_disable_is_idempotent_and_keeps_other_categories_enabled(tmp_path) -> None:
    repository = SqliteSubscriptionRepository(str(tmp_path / "subscriptions.sqlite3"))
    repository.save(category="notice", channel_id="123")
    repository.save(category="event", channel_id="123")

    assert repository.disable(category="notice", channel_id="123") is True
    assert repository.disable(category="notice", channel_id="123") is False
    assert repository.list_enabled(category="notice") == []
    assert [subscription.category for subscription in repository.list_enabled(category="event")] == [
        "event"
    ]


def test_subscription_unique_constraint_keeps_one_row_per_category_and_channel(tmp_path) -> None:
    database_path = tmp_path / "subscriptions.sqlite3"
    repository = SqliteSubscriptionRepository(str(database_path))
    repository.save(category="notice", channel_id="123")
    repository.save(category="notice", channel_id="123")

    with sqlite3.connect(database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM feed_subscriptions").fetchone()[0]
    assert count == 1
