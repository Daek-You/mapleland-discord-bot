CREATE TABLE feed_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    role_id TEXT,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (category, channel_id)
);

CREATE INDEX idx_feed_subscriptions_enabled_category
ON feed_subscriptions (enabled, category);
