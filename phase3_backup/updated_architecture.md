# LiteMigrate — Updated System Architecture (Phase 5 Remediated)

**Date:** November 10, 2026  
**Scope:** Local-first, shadow-verified SQLite migration safety engine (`prototype_shadow_migrate.py`, `database_setup.py`)

---

## 1. End-to-End Lifecycle Architecture

LiteMigrate executes a 6-stage lifecycle designed so that **no unvalidated migration ever touches the user's source SQLite database**, and **no concurrent committed transaction on the source database can ever be silently overwritten**.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: Symlink & Permission Validation + Private Workspace Initialization  │
│  • Reject symlinks on source_db, -wal, -shm, -journal, and shadow_path (S-02)│
│  • Allocate isolated 0o700 temp directory via tempfile.mkdtemp (S-01, S-02)  │
│  • Pre-create shadow file via O_CREAT|O_EXCL|O_NOFOLLOW with 0o600 mode      │
└───────────────────────────────────────┬──────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: WAL-Aware Consistent Shadow Cloning                                 │
│  • Detect active WAL state (journal_mode == WAL or non-empty -wal file)      │
│  • If active WAL or SQLITE_BACKUP_API requested:                             │
│      → Run _bounded_sqlite_backup() via ctypes libsqlite3 with monotonic     │
│        deadline (C-03) and checkpoint/cleanup shadow -wal/-shm (C-04)        │
│  • Else if single-file quiescent DB (DELETE/TRUNCATE/PERSIST):               │
│      → Attempt Linux ioctl(FICLONE) or macOS clonefile(2); fallback to       │
│        _bounded_sqlite_backup() on EXDEV/ENOTSUP                             │
└───────────────────────────────────────┬──────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: Pre-Migration Baseline Snapshot (Purely from Consistent Shadow DB)  │
│  • Open shadow_conn with PRAGMA trusted_schema = OFF verified == 0 (S-03)    │
│  • Compute shadow_baseline_digest = compute_logical_db_digest(shadow_conn)   │
│  • Capture TableSnapshot (row_count, content_sha256, column_sha256s) (D-01)  │
│  • Capture SchemaObjectSnapshot for all indexes, triggers, and views (D-03)  │
└───────────────────────────────────────┬──────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: Transactional Shadow Migration Execution                            │
│  • Configure connection-scoped PRAGMA foreign_keys = OFF/ON outside tx       │
│  • Parse SQL script via sqlite3.complete_statement() accumulator (D-04)      │
│  • Execute statements inside explicit BEGIN ... COMMIT on shadow_conn        │
│  • On any SQLite error: ROLLBACK shadow_conn & return BLOCKED_MIGRATION_EXC  │
└───────────────────────────────────────┬──────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 5: Multi-Invariant Post-Migration Shadow Audit                         │
│  • Re-verify PRAGMA trusted_schema == 0 on shadow_conn (S-03)                │
│  • Run PRAGMA foreign_key_check BEFORE integrity_check (S-04, D-04)          │
│  • Run PRAGMA integrity_check / quick_check                                  │
│  • Compare before/after tables: dropped tables, row losses, whole-table      │
│    content_sha256, and shared-column column_sha256s when columns change(D-01)│
│  • Compare before/after non-table objects: dropped indexes/triggers/views    │
└───────────────────────────────────────┬──────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 6: Zero-TOCTOU Atomic Promotion & Deterministic Cleanup                │
│  • Acquire exclusive flock on <source>.litemigrate.lock (C-01, C-02)         │
│  • Create 0o600 pre-promotion rollback backup of source_db (P-02)            │
│  • Acquire BEGIN IMMEDIATE on source_conn (blocks all SQLite writers)        │
│  • Inside held BEGIN IMMEDIATE: verify compute_logical_db_digest(source_conn)│
│    == shadow_baseline_digest. If mismatch → ROLLBACK & return                │
│    BLOCKED_SOURCE_MODIFIED_CONCURRENTLY (zero lost writes!)                  │
│  • Replay validated SQL statements inside the held BEGIN IMMEDIATE tx on     │
│    source_conn, verify FK + quick_check, and COMMIT atomically (P-02)        │
│  • Update AuditReport (promoted_to_source=True, original_db_untouched=False) │
│  • Unlink shadow files (-wal/-shm/-journal) & rmdir 0o700 workspace in finally│
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystem Designs

### 2.1 Bounded C-API Online Backup Engine (`_bounded_sqlite_backup`)
CPython's built-in `sqlite3.Connection.backup()` calls an internal C loop that invokes `sqlite3_sleep(100)` indefinitely whenever `sqlite3_backup_step()` returns `SQLITE_BUSY` (`5`) or `SQLITE_LOCKED` (`6`), ignoring `PRAGMA busy_timeout`.

LiteMigrate bypasses CPython's unbounded loop by binding directly to `libsqlite3` (`libsqlite3.so.0` on Linux, `libsqlite3.dylib` on macOS) via `ctypes`:
- Extracts the underlying `sqlite3*` database handle from CPython's `pysqlite_Connection` object and verifies pointer alignment via `sqlite3_db_filename(db_ptr, b"main")`.
- Calls `sqlite3_backup_init(dst_db, b"main", src_db, b"main")`.
- Executes `sqlite3_backup_step(backup_ptr, 64)` in a loop guarded by `time.monotonic() >= deadline`.
- If `SQLITE_BUSY` or `SQLITE_LOCKED` persists past `busy_timeout_ms`, immediately calls `sqlite3_backup_finish(backup_ptr)` and raises `sqlite3.OperationalError("database is locked (bounded backup timeout exceeded)")`.

### 2.2 Streaming Per-Table & Per-Column Canonical Digests (`_fingerprint_table_and_columns`)
To keep memory consumption strictly $O(1)$ (`~34 MiB` isolated peak RSS even on an `878.66 MB` database) while preventing `D-01` (column addition masking existing column mutations):
- Rows are streamed in chunks of `1,024` via `SELECT "rowid", *` (or `SELECT *` for `WITHOUT ROWID` tables) ordered deterministically.
- Every cell is serialized with explicit SQLite storage-class prefixes (`N:0:`, `I:<len>:<int>`, `R:8:<ieee754_hex>`, `T:<len>:<utf8>`, `B:<len>:<raw>`).
- In a single table scan, LiteMigrate updates **both** `table_hasher` (whole-row SHA-256) and `col_hashers[col_name]` (per-column SHA-256 concatenated with the row's canonical primary key / rowid prefix so row swaps between keys are also detected per column).
- During post-migration auditing:
  - If `snap_before.column_names == snap_after.column_names`: compares `snap_before.content_sha256 != snap_after.content_sha256`.
  - If `snap_before.column_names != snap_after.column_names` (e.g., `ALTER TABLE ... ADD COLUMN` or `DROP COLUMN`): iterates over `shared_cols = set(snap_before.column_sha256s).intersection(snap_after.column_sha256s)` and flags any table where `snap_before.column_sha256s[col] != snap_after.column_sha256s[col]`.

### 2.3 Non-Table Schema Object Cataloging (`snapshot_schema_objects`)
LiteMigrate queries `sqlite_master` for all user-defined objects where `type IN ('index', 'trigger', 'view') AND name NOT LIKE 'sqlite_%'`, normalizing whitespace in their DDL and recording `(name, obj_type, tbl_name, sql)`. Any dropped index, trigger, or view not explicitly allowlisted in `MigrationPolicy.allowed_dropped_schema_objects` triggers `ValidationVerdict.BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP`.
