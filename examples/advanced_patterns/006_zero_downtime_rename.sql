-- Migration: Safe column rename via table rebuild pattern
CREATE TABLE members_new (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

INSERT INTO members_new (id, full_name, email)
SELECT id, legacy_name, email FROM members;

DROP TABLE members;
ALTER TABLE members_new RENAME TO members;
