# SQLite PRAGMA Optimization Playbook

## 1. Concurrency Optimization
When operating multi-reader workloads, ensure the database is initialized with:
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
```

## 2. Memory & Cache Tuning
- `PRAGMA cache_size = -64000`: Grants 64 MB of page memory.
- `PRAGMA temp_store = MEMORY`: Moves temporary indices and sorting buffers to RAM.
