-- Migration: Rebuild table to expand status check constraint enumeration
CREATE TABLE subscriptions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_tier TEXT NOT NULL CHECK (plan_tier IN ('free', 'starter', 'pro', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('active', 'past_due', 'canceled', 'trialing')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO subscriptions_new (id, user_id, plan_tier, status, created_at)
SELECT id, user_id, plan_tier, status, created_at FROM subscriptions;

DROP TABLE subscriptions;
ALTER TABLE subscriptions_new RENAME TO subscriptions;

CREATE INDEX idx_subscriptions_user_status ON subscriptions(user_id, status);
