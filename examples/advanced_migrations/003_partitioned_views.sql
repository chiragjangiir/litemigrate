-- Migration: Split active events from archived log events via view abstraction
BEGIN TRANSACTION;

CREATE TABLE events_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload TEXT,
    archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW v_recent_events AS
SELECT id, event_type, payload, 'live' AS source FROM events
UNION ALL
SELECT id, event_type, payload, 'archived' AS source FROM events_archive;

COMMIT;
