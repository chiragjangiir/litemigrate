# Advanced SQLite Feature Guide for LiteMigrate

This reference documents support and best practices for modern SQLite features in LiteMigrate:

## 1. Strict Tables (`STRICT`)
SQLite 3.37+ introduces strict type checking:
```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    balance REAL NOT NULL
) STRICT;
```

## 2. Virtual and Stored Generated Columns
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    price REAL NOT NULL,
    tax REAL NOT NULL,
    total REAL GENERATED ALWAYS AS (price + tax) VIRTUAL
);
```

## 3. Partial Indexes
```sql
CREATE INDEX idx_active_users ON users(id) WHERE is_active = 1;
```

## 4. WAL Checkpoint Automation
Use `wal_checkpoint_truncate(conn)` after large batch migrations to reclaim disk space immediately.
