-- Baseline schema with active table and legacy audit table
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    total_cents INTEGER NOT NULL
);

CREATE TABLE legacy_audit_log (
    id INTEGER PRIMARY KEY,
    entry TEXT NOT NULL
);

INSERT INTO orders VALUES (1, 1500), (2, 4200);
INSERT INTO legacy_audit_log VALUES (1, 'Initial setup event');
