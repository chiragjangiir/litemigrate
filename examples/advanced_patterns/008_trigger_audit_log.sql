-- Migration: Create audit trigger logging changes
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_user_audit AFTER INSERT ON users
BEGIN
    INSERT INTO audit_log (action) VALUES ('INSERT_USER');
END;
