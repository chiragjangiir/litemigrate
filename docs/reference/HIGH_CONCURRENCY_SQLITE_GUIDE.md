# High-Concurrency SQLite Production Operations Guide

## 1. Concurrency Model Under WAL Mode
SQLite under `PRAGMA journal_mode = WAL` supports concurrent readers alongside a single writer without read locks blocking write locks.

## 2. Key PRAGMA Performance Settings
- `PRAGMA synchronous = NORMAL`: Balances ACID persistence with minimal fsync overhead.
- `PRAGMA busy_timeout = 5000`: Retries lock acquisitions for up to 5 seconds.
- `PRAGMA cache_size = -64000`: Allocates 64MB of memory page cache.
- `PRAGMA wal_autocheckpoint = 1000`: Flushes WAL pages into the main DB every 1,000 pages.
