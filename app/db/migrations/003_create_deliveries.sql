CREATE TABLE deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_revision_id INTEGER NOT NULL,
    channel_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'sent')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TEXT NOT NULL,
    lease_expires_at TEXT,
    last_error_kind TEXT,
    discord_message_id TEXT,
    sent_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (feed_revision_id, channel_id),
    FOREIGN KEY (feed_revision_id) REFERENCES feed_revisions (id) ON DELETE CASCADE
);

CREATE INDEX idx_deliveries_ready
ON deliveries (status, next_attempt_at, lease_expires_at);
