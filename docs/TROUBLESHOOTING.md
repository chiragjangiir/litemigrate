# SQLite Concurrency & Locking Troubleshooting Guide

## Common Errors
- `sqlite3.OperationalError: database is locked`: Occurs when multiple write connections attempt concurrent locks in DELETE journal mode.
- Resolution: Enable WAL mode (`PRAGMA journal_mode = WAL;`) and increase busy timeout (`PRAGMA busy_timeout = 5000;`).
