# LiteMigrate — System Architecture

LiteMigrate is designed around an uncompromising principle: **no unvalidated migration touches the production database, and no concurrent committed write is ever silently clobbered.**

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Security & Pre-flight Validation                                    │
│    • Reject symlinks (O_NOFOLLOW / is_symlink).                        │
│    • Allocate private 0o700 workspace via tempfile.mkdtemp.            │
│    • Enforce PRAGMA trusted_schema = OFF on all connections.           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Consistent Shadow Database Creation                                 │
│    • If active WAL or backup requested: Bounded libsqlite3 Backup API  │
│    • If single-file quiescent DB: APFS clonefile(2) or Linux FICLONE   │
│    • Mode 0o600 enforced across all clone strategies.                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Baseline Logical Snapshot (from isolated shadow DB)                 │
│    • Compute canonical logical digest across sqlite_master & tables.   │
│    • Capture table row counts, content hashes, and per-column digests. │
│    • Catalog non-table schema objects (indexes, triggers, views).      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Transactional Shadow Migration Execution                            │
│    • Split migration SQL into complete statements via C lexer.         │
│    • Execute statements inside explicit BEGIN ... COMMIT on shadow.    │
│    • Catch errors and rollback cleanly without affecting source.       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. Multi-Invariant Shadow Audit                                        │
│    • PRAGMA foreign_key_check run before integrity checks.             │
│    • PRAGMA integrity_check verifies structural B-tree health.         │
│    • Check for unexpected table drops, row losses, or mutations.       │
│    • Verify surviving views execute without errors.                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 6. CAS Atomic Promotion via BEGIN IMMEDIATE (Optional upon confirm)   │
│    • Acquire advisory POSIX flock on <db>.litemigrate.lock.            │
│    • Create 0o600 pre-promotion rollback backup.                       │
│    • Acquire SQLite write reservation (BEGIN IMMEDIATE) on source.     │
│    • In-transaction CAS check: source live digest == baseline digest.  │
│    • Replay SQL statements inside held lock, verify FKs, and COMMIT.   │
│    • Clean up shadow workspace deterministically.                      │
└────────────────────────────────────────────────────────────────────────┘
```

## Core Subsystems

### 1. Bounded C-API Backup Engine
CPython's built-in `Connection.backup()` contains an unbounded C loop that loops forever on `SQLITE_BUSY` (`sqlite3_sleep(100)`), ignoring `PRAGMA busy_timeout`. LiteMigrate interfaces directly with `libsqlite3` (`sqlite3_open_v2`, `sqlite3_backup_init`, `sqlite3_backup_step`, `sqlite3_backup_finish`) using file paths and monotonic wall-clock deadlines.

### 2. Streaming Row-Identity-Bound Fingerprinting
To detect silent data corruption even when schemas evolve (`ALTER TABLE ... ADD COLUMN`), LiteMigrate streams rows in 1,024-row batches, computing:
- Whole-table canonical SHA-256.
- Per-column SHA-256 concatenated with canonical row identity (`_rowid_` or declared `PRIMARY KEY` columns for `WITHOUT ROWID` tables).
This ensures $O(1)$ memory consumption while mathematically detecting row swaps, rowid reassignments, or value corruptions across shared columns.

### 3. Untrusted Schema Defense
LiteMigrate enforces `PRAGMA trusted_schema = OFF;` and reads back the integer confirmation on every opened connection, neutralizing CVE-2020-13630 attack vectors embedded in malicious schemas or triggers.
