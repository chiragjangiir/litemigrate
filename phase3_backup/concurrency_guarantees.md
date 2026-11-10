# LiteMigrate — Concurrency Protocol & Transactional Guarantees (Phase 5)

**Date:** November 10, 2026  
**Scope:** Formal concurrency specification, zero-TOCTOU promotion protocol (`C-01`, `C-02`), bounded backup locking (`C-03`), and WAL invariance (`C-04`)

---

## 1. Why the Phase 3 Concurrency Protocol Failed

In Phase 3, `prototype_shadow_migrate.py` attempted to protect `source_db` using two decoupled steps:
1. **Window 1 (`C-01`):** `_acquire_source_writer_barrier()` executed `BEGIN IMMEDIATE;` followed immediately by `ROLLBACK;` *before* cloning `source_db`. In SQLite, `ROLLBACK` releases the `RESERVED` lock immediately. Any external writer committing between `ROLLBACK` and `create_shadow_database` (or while the shadow migration ran) modified `source_db` while `source_digest_before` had not yet been taken (or was taken *after* the write, masking the divergence from `shadow_db`).
2. **Window 2 (`C-02`):** Before promotion, Phase 3 checked `compute_file_sha256(source_path) == source_digest_before` in Python user space without holding a SQLite transaction lock, and then called `_promote_shadow_to_source()` which overwrote `source_db` via `shadow_conn.backup(source_conn)`. Any transaction committed by an external writer during the gap between `compute_file_sha256` and `backup()` was **silently overwritten**.

---

## 2. The Phase 5 Zero-TOCTOU Concurrency Protocol

LiteMigrate Phase 5 eliminates both race windows by anchoring baseline verification to the **consistent shadow snapshot** and moving the compare-and-swap (CAS) check **inside the exclusive promotion write transaction**:

```
External SQLite Writer                  LiteMigrate Engine
──────────────────────                  ──────────────────
                                        1. Clone source_db -> shadow_db
                                           (via _bounded_sqlite_backup or FICLONE)
                                        2. Compute shadow_baseline_digest =
                                           compute_logical_db_digest(shadow_db)
  [Case A: Writer commits Tx W1 here]
                                        3. Execute & audit migration on shadow_db
                                        4. Enter _promote_shadow_to_source():
                                           a) Acquire flock(LOCK_EX) on .litemigrate.lock
                                           b) Acquire BEGIN IMMEDIATE on source_conn
  [Case B: Writer attempts Tx W2 here]     ──► SQLite kernel/pager blocks Tx W2!
                                           c) Compute live_source_digest =
                                              compute_logical_db_digest(source_conn)
                                              WHILE HOLDING BEGIN IMMEDIATE!
                                           d) Compare live_source_digest vs
                                              shadow_baseline_digest:
                                              • If Case A occurred:
                                                live_source_digest != shadow_baseline_digest
                                                → ROLLBACK source_conn!
                                                → Return BLOCKED_SOURCE_MODIFIED_CONCURRENTLY
                                                → Tx W1 is 100% preserved!
                                              • If no external write occurred:
                                                live_source_digest == shadow_baseline_digest
                                                → Replay validated migration SQL inside
                                                  the SAME held BEGIN IMMEDIATE tx!
                                                → Verify FK + quick_check
                                                → COMMIT source_conn atomically!
                                           e) Release BEGIN IMMEDIATE & flock
```

---

## 3. Exact Guarantees & Known Limitations

### 3.1 Proven Guarantees (Verified by Automated Tests)
1. **Zero Silent Write Overwrites (`C-01`, `C-02`):** No committed transaction from any SQLite-compliant external process (whether it uses LiteMigrate's `.litemigrate.lock` or standard SQLite locking without cooperating with `.litemigrate.lock`) can ever be silently overwritten.
   - **Why this holds even for uncooperative external SQLite processes:** Step 4b (`BEGIN IMMEDIATE` on `source_conn`) acquires SQLite's native pager-level `RESERVED` lock on `source_db`. Every SQLite connection in any process must acquire `RESERVED` before modifying the database or appending to `-wal`. Once LiteMigrate holds `BEGIN IMMEDIATE` on `source_conn`, no external SQLite connection can commit a write until LiteMigrate either commits or rolls back. Because `compute_logical_db_digest(source_conn)` runs *after* `BEGIN IMMEDIATE` is acquired, any write committed *before* `BEGIN IMMEDIATE` is guaranteed to be visible to `source_conn` and detected as a mismatch against `shadow_baseline_digest`, triggering an immediate `ROLLBACK`.
2. **Bounded Lock Acquisition & Backup Execution (`C-03`):** Every lock acquisition (`flock`, `BEGIN IMMEDIATE`) and every page-copy loop (`_bounded_sqlite_backup` via `ctypes` `sqlite3_backup_step`) is governed by a monotonic deadline (`policy.busy_timeout_ms`). If an external process holds an unyielding write lock beyond `busy_timeout_ms`, LiteMigrate aborts cleanly with `ValidationVerdict.BLOCKED_CONCURRENT_LOCK`.
3. **WAL Checkpoint Invariance (`C-04`):** Because `compute_logical_db_digest()` hashes the canonical schema catalog (`sqlite_master`) and canonical per-table content digests rather than physical file bytes, background or passive WAL checkpoints (`PRAGMA wal_checkpoint(PASSIVE/TRUNCATE)`) never cause false-positive CAS aborts.
4. **Multi-Process LiteMigrate Serialization (`test_12`):** Two concurrent LiteMigrate processes targeting the same `source_db` coordinate via `<source_db>.litemigrate.lock` (`fcntl.flock`) and `BEGIN IMMEDIATE`, ensuring either clean serialization or safe `BLOCKED_SOURCE_MODIFIED_CONCURRENTLY` / `BLOCKED_CONCURRENT_LOCK` rejection without corrupting the database or losing either migration's committed state.

### 3.2 Documented Limitations
1. **Optimistic Validation Window:** Because LiteMigrate does not hold `BEGIN IMMEDIATE` on `source_db` during the potentially multi-second shadow migration and SHA-256 audit (doing so would block production writers for the entire duration of the shadow audit), a concurrent write to `source_db` while the shadow audit is running will cause promotion to abort safely with `BLOCKED_SOURCE_MODIFIED_CONCURRENTLY`. The caller must retry the migration during a quieter write window.
2. **Non-SQLite Raw File Writers:** If a non-SQLite rogue process bypasses the SQLite library entirely and writes raw bytes directly to the `.db` file descriptor without acquiring SQLite locks or POSIX locks, OS-level file corruption can occur outside SQLite's concurrency model.
3. **Callable Promotion Fallback:** When a migration is provided as an arbitrary Python `Callable[[sqlite3.Connection], None]` with `disable_foreign_keys_during_migration=True` (which cannot change `PRAGMA foreign_keys` mid-transaction), `_promote_shadow_to_source` verifies the CAS digest inside `BEGIN IMMEDIATE`, creates a `0o600` rollback backup, and promotes via `_bounded_sqlite_backup()` while holding the `.litemigrate.lock` advisory lock. SQL script migrations (`Sequence[str]`, the primary workflow) execute 100% inside the single held `BEGIN IMMEDIATE` transaction.
