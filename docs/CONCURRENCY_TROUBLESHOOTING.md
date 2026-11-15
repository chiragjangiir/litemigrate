# SQLite Concurrency & Locking Troubleshooting

Resolving lock contention (`database is locked`) in multi-process SQLite environments.

---

## 1. Verify WAL Mode
Confirm `PRAGMA journal_mode=WAL;` is enabled across all connecting application nodes.
