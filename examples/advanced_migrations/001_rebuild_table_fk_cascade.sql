-- Migration: Rebuild table with foreign key constraints and cascade actions
-- Demonstrates the canonical 12-step SQLite table rebuild pattern

-- 1. Create new table with updated constraints and default values
CREATE TABLE orders_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0),
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. Migrate existing records
INSERT INTO orders_new (id, user_id, total_cents, currency, status, created_at)
SELECT id, user_id, total_cents, 'USD', status, created_at FROM orders;

-- 3. Drop legacy table
DROP TABLE orders;

-- 4. Rename new table to original target
ALTER TABLE orders_new RENAME TO orders;

-- 5. Recreate indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
