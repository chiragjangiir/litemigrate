# LiteMigrate — Implementation Gaps & Technical Reconciliation Report

**Date:** November 10, 2026  
**Document Purpose:** Formal record of discrepancies between Phase 5 documentation and source code, along with required engineering resolutions for MVP production readiness.

---

## Gap A: Callable Migration Handling & Source Transaction Safety

### The Discrepancy
In `prototype_shadow_migrate.py:1217–1219`:
```python
if callable(migration_sql_or_callable):
    source_conn.execute("COMMIT;")
    migration_sql_or_callable(source_conn)
```
The prototype opens `source_conn`, acquires `BEGIN IMMEDIATE;`, verifies `live_digest == expected_source_digest`, but then **commits the source transaction immediately before invoking the callable migration**.

### Failure Modes & Hazards
1. **Loss of Atomicity:** If the Python callable fails halfway through its work or raises an exception, the changes made up to that point remain committed on the source database.
2. **Lost Concurrency Protection:** Once `COMMIT;` is executed, SQLite's `RESERVED`/`EXCLUSIVE` writer lock is released. External writers can interleave writes while the callable runs, violating serializability.
3. **Foreign Key Inconsistency:** If `disable_foreign_keys=True` was passed, foreign keys cannot be toggled inside an active transaction, but releasing the transaction leaves foreign keys in an altered state outside transaction boundaries.

### Resolution for MVP
- **Primary Migration Interface:** SQL migration scripts (single string or sequence of statements) executed inside an atomic `BEGIN IMMEDIATE ... COMMIT` block.
- **Explicit Rejection:** The public API (`litemigrate.engine` and CLI) will explicitly reject arbitrary Python callables with a descriptive `UnsupportedMigrationTypeError`.
- **Regression Test:** Add regression test proving that arbitrary callables cannot partially modify the source database or bypass atomicity guarantees.

---

## Gap B: Data Fingerprint Correctness & Canonical Row Identity

### The Discrepancy
In `updated_architecture.md` Section 2.2:
> *"LiteMigrate updates both table_hasher (whole-row SHA-256) and col_hashers[col_name] (per-column SHA-256 concatenated with the row's canonical primary key / rowid prefix so row swaps between keys are also detected per column)."*

However, in `prototype_shadow_migrate.py:263–268`:
```python
for row in batch:
    for idx, cell in enumerate(row):
        cb = _canonical_cell_bytes(cell)
        table_hasher.update(cb)
        col_hashers[idx].update(cb)
    table_hasher.update(b"\n")
```
`col_hashers[idx]` updates strictly with `cb` (the raw cell value), completely omitting the row's canonical identity.

### Failure Modes & Hazards
1. **Row Permutation & Swap Collisions:** If two rows swap column values (e.g., Alice and Bob swap `email` addresses or `account_balance`), `col_hashers` for that column will produce the exact same digest because SHA-256 accumulates values in sequence, but without row identity binding, inter-row correlation is degraded.
2. **`WITHOUT ROWID` Tables:** `SELECT ... ORDER BY rowid` fails with `OperationalError: no such column: rowid` on `WITHOUT ROWID` tables. The fallback `ORDER BY <all_columns>` is expensive and does not bind column hashes to the explicit primary key.

### Requirements for Correct Implementation
1. **Canonical Row Identity Prefix:**
   - For standard tables: Query `rowid` as canonical row identity (`R:<int64>:`).
   - For `WITHOUT ROWID` tables: Query the declared `PRIMARY KEY` columns in declaration order and serialize them canonically (`PK:<cell1>:<cell2>...`).
   - If a table lacks an identifiable stable primary key or rowid (or is a virtual table with non-deterministic row ordering), raise an explicit `UnsupportedTableStructureError` rather than silently degrading validation.
2. **Column Hasher Binding:**
   For each cell at index `idx` for column `col_name`, update:
   `col_hashers[col_name].update(row_identity_bytes + b":" + cell_bytes + b"\n")`.
3. **Deterministic Sorting:**
   Enforce deterministic row sorting (`ORDER BY rowid` or `ORDER BY pk_col1, pk_col2...`).
4. **Comprehensive Test Matrix:**
   Unit tests for:
   - Rowid changes and row reordering.
   - `WITHOUT ROWID` tables with single and composite primary keys.
   - `NULL` values, BLOBs, signed floating-point zero (`-0.0` vs `+0.0`).
   - Adding and dropping columns.

---

## Gap C: Concurrency and Promotion Guarantees

### Analysis of Boundaries
- **SQLite-Compliant Writers:** Protected via `BEGIN IMMEDIATE` acquired before the CAS check and held through SQL execution and commit. No TOCTOU window exists for SQLite-cooperating writers.
- **Concurrent LiteMigrate Processes:** Protected via exclusive non-blocking `fcntl.flock` on `<db>.litemigrate.lock`.
- **Non-SQLite Rogue Writers:** If an external process writes raw bytes directly into the `.db` file descriptor without acquiring SQLite locks, SQLite cannot prevent file tearing. This must be clearly documented as an out-of-scope threat boundary.
- **Optimistic Validation Window:** LiteMigrate does not hold an exclusive lock during shadow validation (to avoid locking production writers during long validations). If an external writer commits to `source_db` during validation, promotion cleanly detects `live_digest != expected_digest` and rolls back with `BLOCKED_SOURCE_MODIFIED_CONCURRENTLY`.

---

## Gap D: Security Hardening

1. **Untrusted Schema:** Enforce `PRAGMA trusted_schema = OFF;` on all opened connections and verify read-back equals `0`.
2. **Symlink Traversal Prevention:** Strictly reject symlinks across source database, shadow database, lock files, and rollback backup files using `os.O_NOFOLLOW` and `path.is_symlink()`.
3. **Workspace Isolation:** Shadow databases must only be allocated inside `0o700` temporary directories created with `tempfile.mkdtemp()`.
4. **File Modes:** All created database copies, backups, and lock files must be explicitly created with `0o600` (`-rw-------`).
5. **Identifier Quoting:** Escape all table and column names with double quotes using `name.replace('"', '""')`.

---

## Gap E: Native SQLite & ctypes Integration

- **Honest Documentation:** Clarify that `_bounded_sqlite_backup` invokes `sqlite3_open_v2` on the source and destination filesystem paths, rather than extracting CPython internal connection pointers.
- **Resource Management:** Ensure that `sqlite3_backup_finish`, `sqlite3_close_v2`, and file descriptors are unconditionally cleaned up even under Python exceptions or task cancellation.
- **Platform Detection:** Support both Linux `libsqlite3.so.0` and macOS `libsqlite3.dylib` dynamically via `ctypes.util.find_library("sqlite3")`.

---

## Gap F: Platform Clone Strategies

- **Linux XFS/Btrfs:** `FICLONE` (`ioctl 0x40049409`).
- **macOS APFS:** `clonefile(2)` via Darwin libc with `CLONE_NOFOLLOW`. Verified working natively on Apple Silicon APFS.
- **Universal POSIX Fallback:** `SQLITE_BACKUP_API` with monotonic deadline.
- **No Masquerading:** The engine must accurately report the exact clone strategy used in the audit report (`strategy_used`).
