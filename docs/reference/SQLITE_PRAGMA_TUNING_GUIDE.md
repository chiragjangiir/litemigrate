# SQLite PRAGMA Production Tuning Guide

## Recommended High-Performance Settings
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA temp_store = MEMORY;
PRAGMA cache_size = -64000; -- 64MB cache
PRAGMA busy_timeout = 5000;
```
