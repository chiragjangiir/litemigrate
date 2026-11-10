# LiteMigrate — Concurrency Protocol & Transactional Guarantees

LiteMigrate guarantees that **no committed transaction from any cooperating SQLite writer is ever silently overwritten during migration.**

## Concurrency Lifecycle

```
External SQLite Writer               LiteMigrate Engine
──────────────────────               ──────────────────
                                     1. Clone source_db -> shadow_db
                                        (APFS clonefile or Bounded Backup)
                                     2. Capture shadow_baseline_digest
  [Writer commits Tx W1 here]
                                     3. Execute & audit migration on shadow_db
                                     4. Enter promotion:
                                        a) Acquire flock on <source>.litemigrate.lock
                                        b) Open source_conn & BEGIN IMMEDIATE
  [Writer attempts Tx W2 here] ──► Blocked by SQLite RESERVED/EXCLUSIVE lock!
                                        c) Compute live_source_digest
                                           WHILE HOLDING BEGIN IMMEDIATE!
                                        d) Compare live vs baseline:
                                           • Mismatch detected! (Tx W1 occurred)
                                             → ROLLBACK source_conn
                                             → Return BLOCKED_SOURCE_MODIFIED_CONCURRENTLY
                                             → Tx W1 is 100% PRESERVED!
                                           • Matches baseline:
                                             → Replay migration inside held transaction
                                             → Verify FKs and quick_check
                                             → COMMIT source_conn atomically!
```

## Exact Guarantees

### 1. SQLite-Cooperating External Writers
When an external application writes through SQLite (with rollback journal or WAL):
- If the write commits before LiteMigrate acquires `BEGIN IMMEDIATE` on promotion, `live_source_digest` differs from `shadow_baseline_digest`. LiteMigrate rolls back immediately, preserving the external write.
- If the write attempts to commit after LiteMigrate acquires `BEGIN IMMEDIATE`, SQLite's pager blocks the external writer until LiteMigrate commits or rolls back.

### 2. Multi-Process LiteMigrate Coordination
Two concurrent LiteMigrate invocations coordinate using POSIX advisory locks on `<database>.litemigrate.lock`. The second process waits up to `busy_timeout_ms` before exiting with `BLOCKED_CONCURRENT_LOCK`.

### 3. Non-SQLite Direct File Modifiers (Boundary Limitation)
If a process outside SQLite directly opens `<db>.sqlite` with `open()` and writes raw bytes to disk bypassing SQLite locks, filesystem-level corruption may occur. LiteMigrate cannot guard against out-of-band kernel/filesystem tampering.
