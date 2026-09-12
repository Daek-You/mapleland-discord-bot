CREATE TABLE feed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    category TEXT NOT NULL,
    external_id TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    published_at TEXT,
    source_updated_at TEXT,
    current_content_hash TEXT NOT NULL,
    last_checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active',
    UNIQUE (source, external_id)
);

CREATE INDEX idx_feed_items_category_status
ON feed_items (category, status);

CREATE TABLE feed_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_item_id INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    discovered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notification_required INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (feed_item_id) REFERENCES feed_items (id) ON DELETE CASCADE
);

CREATE INDEX idx_feed_revisions_item_discovered
ON feed_revisions (feed_item_id, discovered_at);
