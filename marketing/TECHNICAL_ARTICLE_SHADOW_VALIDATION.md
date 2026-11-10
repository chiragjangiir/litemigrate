# Shadow Database Validation Explained: How LiteMigrate Enforces Invariants

When software engineers test code, we run unit tests in isolated sandboxes. When we test APIs, we use mock servers. But when we test database migrations, we all too often execute SQL scripts directly against staging or production databases and hope for the best.

**LiteMigrate** introduces **shadow validation** for SQLite: creating an instantaneous, isolated copy-on-write clone of an active SQLite database, applying the migration inside the sandbox, auditing all relational and data invariants, and promoting changes to the source database only after validation succeeds.

In this technical breakdown, we look at how shadow validation is implemented under the hood: from filesystem copy-on-write primitives to streaming row fingerprinting and atomic Compare-And-Swap (CAS) promotion.

---

## 1. The Cloning Layer: Sub-Millisecond Reflinks & WAL Safety

Creating a copy of an active database usually presents two challenges:
1. **Performance**: Traditional `cp` or file streaming copies every byte from source to destination. On a 10 GB database, copying takes seconds to minutes and consumes 10 GB of additional disk space.
2. **Consistency**: If a database is in WAL (Write-Ahead Logging) mode with uncheckpointed frames, copying the main `.db` file without copying `-wal` and `-shm` yields an inconsistent, torn database state.

### How LiteMigrate Solves Both:

LiteMigrate implements a tiered cloning architecture:

```
[ Active SQLite DB ]
        │
        ├── Is WAL mode active with uncheckpointed frames?
        │       │
        │       ├── YES ──► Use SQLite Online Backup API (sqlite3_backup_*)
        │       │           (Flushes WAL frames into clean, defragmented pages)
        │       │
        │       └── NO  ──► Is filesystem Reflink supported?
        │                       │
        │                       ├── macOS (APFS)  ──► clonefile(2) (< 1 ms)
        │                       ├── Linux (XFS/Btrfs) ──► ioctl(FICLONE) (< 1 ms)
        │                       └── Other / Fallback ──► sqlite3_backup_*
```

### Reflinks (Copy-on-Write)
On macOS APFS and Linux filesystems supporting `FICLONE` (Btrfs, XFS), LiteMigrate issues kernel copy-on-write calls. Instead of duplicating data blocks on disk, the filesystem creates a new inode whose extents point to the original physical blocks. 

- **Time taken**: Under **0.5 milliseconds**, regardless of database size.
- **Disk consumption**: Zero additional disk space allocated until pages are modified by the migration.

### WAL Safety & Transactional Consistency
If the database has active WAL frames, raw filesystem reflinks could capture an incomplete checkpoint. LiteMigrate inspects the `-wal` file size. If uncheckpointed transactions exist, LiteMigrate invokes the official **SQLite Online Backup API** (`sqlite3_backup_init`, `sqlite3_backup_step`), which streams consistent, locked database pages into the shadow file without blocking active readers or writers.

---

## 2. The Invariant Verification Engine

Once the shadow database is instantiated, LiteMigrate executes the migration SQL inside the shadow environment and runs a comprehensive multi-invariant audit.

```
       [ Shadow Database ]
                │
    ┌───────────┴───────────┐
    ▼                       ▼
1. Structural Audit     2. Data Continuity Audit
   • PRAGMA integrity      • Streaming Row Fingerprints
   • PRAGMA foreign_key    • Column Storage Class Hashes
   • View / Trigger Diff   • Policy Enforcement
```

### A. Physical Integrity & Foreign Keys
LiteMigrate immediately runs:
```sql
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```
If a foreign key constraint is violated anywhere in the schema—even in tables that were not directly mentioned in the migration script—LiteMigrate catches the offending row ID and child table name.

### B. Streaming Row Fingerprinting
To detect silent data corruption, LiteMigrate fingerprints table contents before and after migration.

Computing a single global database checksum is insufficient because an additive migration (like `ALTER TABLE users ADD COLUMN age INT;`) deliberately modifies schema definitions. Instead, LiteMigrate tracks **row-level invariant continuity**:

1. **Storage Class Discrimination**: SQLite stores values in five basic classes: `NULL`, `INTEGER`, `REAL`, `TEXT`, and `BLOB`. LiteMigrate serializes each cell canonically into raw typed bytes:
   - Floats: Encoded as 8-byte IEEE-754 big-endian doubles. Crucially, `0.0` and `-0.0` are discriminated rather than treated as identical.
   - Integers: Serialized to 8-byte signed big-endian.
   - Text: UTF-8 encoded with length prefixes.
   - Blobs: Raw bytes with length prefixes.
2. **Rowid vs. WITHOUT ROWID Handling**:
   - For standard rowid tables, row identity is bound to `rowid`. If a user table defines explicit columns named `rowid`, `_rowid_`, or `oid`, LiteMigrate detects the column aliasing to prevent hash collisions.
   - For `WITHOUT ROWID` tables, LiteMigrate queries `PRAGMA table_info` and binds row identity to the ordered primary key columns.
3. **Streaming Memory Efficiency**: Rather than loading millions of rows into Python memory, rows are processed in fixed batch sizes (1,000 rows per chunk) with rolling SHA-256 digests.

### C. Policy Enforcement
LiteMigrate enforces a strict default policy: **no table, column, view, trigger, or index may be dropped or truncated without explicit authorization.**

If a migration drops a legacy audit table:
```sql
DROP TABLE legacy_audit;
```
LiteMigrate detects the missing table in the post-migration schema diff and halts promotion with:
```text
Verdict: BLOCKED_UNEXPECTED_TABLE_DROP
Details: Unexpected dropped table 'legacy_audit' was not declared in policy.allowed_dropped_tables.
```
To permit the drop, the developer must provide an explicit, version-controlled `policy.json`:
```json
{
  "allowed_dropped_tables": ["legacy_audit"],
  "allowed_row_loss_tables": ["legacy_audit"]
}
```

---

## 3. Concurrency-Safe Promotion: Compare-And-Swap (CAS)

The most subtle risk in database migrations is the **Time-of-Check to Time-of-Use (TOCTOU)** window: what happens if someone writes to the live database while you were validating on the shadow copy?

LiteMigrate solves this using an atomic Compare-And-Swap protocol:

```
Step 1: On Shadow Creation
        Record: Baseline Source Digest & PRAGMA data_version

Step 2: On `litemigrate apply --confirm`
        Acquire Exclusive Writer Lock: BEGIN IMMEDIATE;
        
Step 3: CAS Check Under Exclusive Lock
        Check: Live Source data_version == Baseline data_version?
        Check: Live Source Digest == Baseline Source Digest?
        
        ├── IF CHANGED: ROLLBACK; Abort with ConcurrencyConflictError!
        │               (Zero lost updates. Live database preserved.)
        │
        └── IF UNCHANGED:
                Create timestamped pre-migration backup (.bak)
                Apply validated migration SQL
                COMMIT;
```

By verifying the live source state inside `BEGIN IMMEDIATE` before committing changes, LiteMigrate guarantees that concurrent transactions committed during the validation window are never clobbered.

---

## 4. Structured Machine-Readable Output

LiteMigrate produces both a human-readable terminal summary and a complete JSON audit report:

```json
{
  "verdict": "passed",
  "details": [
    "Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied."
  ],
  "original_db_path": "app.db",
  "promoted_to_source": true,
  "backup_path": "app.db.pre_migrate_1794311745.bak",
  "clone_result": {
    "strategy_used": "apfs_clonefile",
    "duration_ms": 0.33
  },
  "foreign_key_violations": [],
  "integrity_check_passed": true,
  "total_elapsed_ms": 7.10
}
```

This report can be checked into version control alongside migration scripts or parsed by continuous deployment runners to gate automated deployments.

---

## Try LiteMigrate Today

LiteMigrate is an open-source, local-first utility for developers who demand high reliability from their SQLite infrastructure.

- **GitHub Repository**: [https://github.com/chiragjangiir/litemigrate](https://github.com/chiragjangiir/litemigrate)
- **Current Release**: `v0.1.0-alpha.1` (Experimental Alpha)
- **License**: Apache-2.0

