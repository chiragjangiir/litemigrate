-- Baseline schema for basic migration example
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (id, username, email) VALUES
    (1, 'alice', 'alice@example.com'),
    (2, 'bob', 'bob@example.com');
