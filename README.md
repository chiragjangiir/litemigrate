# LiteMigrate

> **Safer SQLite migrations through shadow verification.**

[![CI Tests](https://github.com/chiragjangiir/litemigrate/actions/workflows/tests.yml/badge.svg)](https://github.com/chiragjangiir/litemigrate/actions/workflows/tests.yml)
[![Lint & Typecheck](https://github.com/chiragjangiir/litemigrate/actions/workflows/lint.yml/badge.svg)](https://github.com/chiragjangiir/litemigrate/actions/workflows/lint.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha_RC1-orange.svg)](RELEASE_READINESS.md)

---

> [!WARNING]
> **LiteMigrate is currently an experimental Alpha release (`v0.1.0-alpha.1`).**
> It is designed to assist developers and teams in catching destructive migration bugs early. **Never test or run migrations on the sole copy of important production data.** Always maintain verified, independent off-site backups before applying schema changes to any live database.

---

## What LiteMigrate Does

LiteMigrate is a local-first, zero-cloud CLI tool and Python library for SQLite migration safety. It allows developers to test database migrations against an isolated, copy-on-write shadow copy of their real database, verify that all data and relational invariants survived, and promote the migration to the live database only after all safety checks pass.

### The Problem LiteMigrate Solves

SQLite is increasingly used for mission-critical applications: embedded devices, mobile apps, local-first architectures, and production web backends (via WAL mode). However, schema migrations in SQLite are prone to silent, irreversible failures that traditional migration runners ignore:

1. **Foreign Key Cascade Wipes ([ariga/atlas #3317](https://github.com/ariga/atlas/issues/3317)):** When rebuilding a table with foreign keys active, executing `DROP TABLE parent` cascades and silently deletes every child record across related tables without warning or syntax errors.
2. **Silent Column Data Mutations:** Adding a column while accidentally resetting, truncating, or altering existing column data often executes successfully in SQL runners while silently corrupting rows.
3. **Lost Updates Under Live Concurrency:** Applying a migration to an active SQLite database while external processes are committing transactions can lead to lost updates or corrupted state if writer leases and compare-and-swap (CAS) barriers are not enforced.
4. **Invalidated Triggers and Views:** Dropping or renaming a table can leave surviving triggers or views broken, causing application queries to crash later in production.

Most migration tools report success as long as SQLite executes the SQL without syntax errors. **LiteMigrate verifies that your data actually survived.**

---

## Core Lifecycle

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Security & Pre-flight Inspection                                    │
│    • Rejects symlinks on source, shadow, and backup paths.             │
│    • Allocates an isolated 0o700 temporary workspace.                  │
│    • Enforces PRAGMA trusted_schema = OFF on all connections.          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Consistent Shadow Database Creation                                 │
│    • Active WAL: Bounded libsqlite3 Backup API with deadline.          │
│    • Quiescent DB: macOS APFS clonefile(2) or Linux FICLONE ioctl.     │
│    • Private 0o600 permissions enforced on shadow database.            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Baseline Snapshot (from isolated shadow copy)                       │
│    • Streaming row-identity-bound SHA-256 fingerprinting.              │
│    • Table row counts, content hashes, and per-column digests.         │
│    • Schema inventory (tables, indexes, triggers, views).              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Transactional Shadow Migration Execution                            │
│    • Splits SQL into complete statements via SQLite lexer.             │
│    • Executes inside explicit BEGIN ... COMMIT on shadow copy.         │
│    • Source database remains 100% untouched.                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. Multi-Invariant Shadow Audit                                        │
│    • PRAGMA foreign_key_check run before integrity checks.             │
│    • PRAGMA integrity_check verifies B-tree structural health.         │
│    • Checks for unexpected drops, row losses, and column mutations.   │
│    • Verifies surviving views and triggers parse and execute.          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 6. Zero-TOCTOU Atomic Promotion (apply --confirm)                      │
│    • Acquires advisory lock on <source>.litemigrate.lock.              │
│    • Creates 0o600 pre-promotion rollback backup.                      │
│    • Acquires BEGIN IMMEDIATE writer lease on source connection.       │
│    • In-transaction CAS: re-verifies live source matches baseline.     │
│    • Replays SQL inside held lock, verifies FKs, and COMMITs.          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

LiteMigrate is local-first with **zero required external dependencies** outside Python's standard library and the platform's SQLite C library (`libsqlite3`).

### From Local Project or Repository:
```bash
git clone https://github.com/chiragjangiir/litemigrate.git
cd litemigrate
python3 -m pip install -e .
```

### From Wheel:
```bash
python3 -m pip install dist/litemigrate-0.1.0a1-py3-none-any.whl
```

**Requirements:**
- Python `>= 3.9`
- SQLite `>= 3.35.0` (bundled with Python on most modern platforms)

---

## 60-Second Disposable Quick-Start

You can test LiteMigrate right now on disposable databases without touching real project data.

### Step 1: Create a Disposable Database
```bash
mkdir -p /tmp/litemigrate_demo && cd /tmp/litemigrate_demo

python3 -c "
import sqlite3
conn = sqlite3.connect('demo.db')
conn.execute('CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT);')
conn.execute('CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INT, FOREIGN KEY (parent_id) REFERENCES parent(id) ON DELETE CASCADE);')
conn.execute('INSERT INTO parent VALUES (1, \"Alpha\"), (2, \"Beta\");')
conn.execute('INSERT INTO child VALUES (10, 1), (20, 2);')
conn.commit()
conn.close()
"
```

### Step 2: Inspect Database Health
```bash
litemigrate inspect --db demo.db
```
*Output: Displays database size, SQLite version, journal mode, tables (`parent`, `child`), and integrity status without printing table contents.*

### Step 3: Validate a Safe Migration (Column Addition)
```bash
echo "ALTER TABLE parent ADD COLUMN description TEXT DEFAULT 'none';" > safe_migration.sql

litemigrate validate --db demo.db --migration safe_migration.sql
```
*Result: **`Verdict: PASSED`**. LiteMigrate cloned `demo.db` to an isolated shadow copy, verified the migration, audited all invariants, and left `demo.db` 100% untouched.*

### Step 4: Validate a Dangerous Migration (Cascade Wipe Reproduction)
Now test what happens when a migration attempts an unsafe table drop:
```bash
cat << 'EOF' > dangerous_migration.sql
DROP TABLE parent;
CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT, extra TEXT);
EOF

litemigrate validate --db demo.db --migration dangerous_migration.sql
```
*Result: **`Verdict: BLOCKED_UNEXPECTED_ROW_LOSS`** / **`BLOCKED_UNEXPECTED_TABLE_DROP`**. LiteMigrate catches that dropping `parent` wiped rows in `child` and blocked the migration before it could ever touch your source database!*

### Step 5: Apply a Validated Migration Safely
```bash
litemigrate apply --db demo.db --migration safe_migration.sql --confirm
```
*Result: LiteMigrate validates on shadow, acquires an exclusive writer lease, creates a `demo.db.pre_migrate_<timestamp>.bak` recovery backup, re-verifies source integrity via CAS, and atomically commits the change.*

---

## CLI Reference

### `litemigrate inspect`
Inspects database schema, journal mode, foreign key status, table count, and integrity metadata without displaying sensitive row contents.
```bash
litemigrate inspect --db <path-to-db> [--json]
```

### `litemigrate validate`
Clones an isolated shadow copy using copy-on-write reflink (APFS on macOS, FICLONE on Linux) or the SQLite Backup API. Executes the migration inside the shadow database and runs a multi-invariant audit.
```bash
litemigrate validate --db <path-to-db> --migration <path-to-sql> [--policy <path-to-policy.json>] [--output report.json] [--json]
```
*Guarantees: **The source database is never modified during validation.***

### `litemigrate apply`
Validates the migration on the shadow copy first. Requires explicit confirmation (`--confirm` flag or interactive prompt). Creates a timestamped pre-promotion backup file (`.bak`). Acquires an exclusive writer lock (`BEGIN IMMEDIATE`) on the source database, checks the CAS baseline digest to ensure no concurrent writes occurred, applies the migration, and commits atomically.
```bash
litemigrate apply --db <path-to-db> --migration <path-to-sql> --confirm [--policy <path-to-policy.json>] [--output report.json] [--json]
```

### `litemigrate report`
Reads and formats previously generated audit JSON reports into terminal summaries or formatted JSON.
```bash
litemigrate report --input report.json [--json]
```

---

## What Happens When Validation Fails?

When a migration violates any safety invariant:
1. **The Source Database Remains 100% Untouched:** All mutations occurred inside an isolated temporary directory.
2. **The Shadow Database is Cleanly Discarded:** Temporary databases and lock files are deterministically cleaned up.
3. **A Clear Audit Report is Emitted:** LiteMigrate identifies the exact table, column, or foreign key violation causing the failure.
4. **A Non-Zero Exit Code is Returned:** Allowing CI pipelines and deployment scripts to immediately halt.

### Exit Codes

| Exit Code | Verdict | Meaning |
| :---: | :--- | :--- |
| **`0`** | `PASSED` | All safety invariants satisfied; migration applied or validated. |
| **`1`** | `BLOCKED_*` | Invariant violation (unexpected row loss, drop, mutation, or FK violation). |
| **`2`** | `BLOCKED_CONCURRENT_*` | Concurrent writer detected during promotion or lock timeout exceeded. |
| **`3`** | `Security Error` | Symlink detected, permission invalid, or unsafe path. |
| **`4`** | `Aborted / Unconfirmed` | Interactive confirmation declined or `--confirm` missing in non-interactive environment. |
| **`5`** | `Execution Error` | Migration SQL syntax error or SQLite execution exception. |

---

## Backup, Concurrency & Recovery

### Pre-Promotion Backup
Whenever `litemigrate apply` executes, a consistent backup is created prior to promotion:
```
<database_path>.pre_migrate_<unix_nanoseconds>.bak
```
- Permissions are strictly set to `0o600` (readable only by the database owner).
- To manually restore if an external deployment issue arises:
  ```bash
  cp app.db.pre_migrate_1794308039305443000.bak app.db
  ```

### Concurrency Protection & CAS Barrier
LiteMigrate distinguishes between two types of concurrent processes:
- **SQLite-Cooperating Writers:** Any process connecting via SQLite that writes to the database will increment SQLite change counters. LiteMigrate re-computes the source digest inside its held `BEGIN IMMEDIATE` lock. If any concurrent transaction committed after shadow cloning, promotion aborts with `BLOCKED_SOURCE_MODIFIED_CONCURRENTLY` to avoid lost updates.
- **Non-SQLite Rogue Writers:** If an external process writes raw bytes directly into the `.db` file descriptor (bypassing SQLite's file-locking protocol), filesystem corruption cannot be prevented by SQLite VFS locks.

---

## Safety Policy Configuration

By default, LiteMigrate denies all destructive changes:
- Table drops are blocked.
- Row deletions are blocked.
- Column data mutations on existing columns are blocked.
- Dropping views, triggers, or indexes is blocked.

When a schema migration intentionally removes or archives data, provide a JSON policy:
```json
{
  "allowed_dropped_tables": ["legacy_session_log"],
  "allowed_row_loss_tables": ["archived_orders"],
  "allowed_mutated_tables": [],
  "allowed_dropped_views": [],
  "allowed_dropped_triggers": [],
  "allowed_dropped_indexes": [],
  "disable_foreign_keys_during_migration": true,
  "busy_timeout_ms": 3000
}
```
Pass with `--policy ./policy.json`.

---

## Empirically Tested Environments

The automated test suite runs across an 8-platform matrix in GitHub Actions on every push:

| Platform | Architecture | Python Versions | Filesystem / Shadow Clone |
| :--- | :--- | :--- | :--- |
| **macOS Darwin (14 / 15 / 26)** | Apple Silicon arm64 | 3.9, 3.10, 3.11, 3.12 | APFS `clonefile(2)` copy-on-write (~1.2 ms clone) |
| **Ubuntu Linux (22.04 / 24.04)** | x86_64 | 3.9, 3.10, 3.11, 3.12 | `ioctl(FICLONE)` on XFS/Btrfs; SQLite Backup API on ext4 |

### Tested SQLite Versions
- SQLite `3.37.2` through `3.53.4`
- Tested with both `WAL` (Write-Ahead Logging) and `DELETE` rollback journal modes.

---

## Known Limitations

- **SQLite Only:** LiteMigrate is intentionally engineered for SQLite. PostgreSQL, MySQL, DuckDB, and LibSQL are not supported.
- **SQL Scripts Only:** Python callables are explicitly rejected by design; callables cannot be rolled back atomically under SQLite transaction boundaries.
- **Stable Row Identity Required:** Standard rowid tables and `WITHOUT ROWID` tables with primary keys are supported. Tables shadowing `rowid`, `_rowid_`, and `oid` simultaneously without a primary key cannot be deterministically verified and are rejected.
- For complete operational boundaries, see [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md).

---

## Running the Test Suite

```bash
# Run all 62 unit, integration, and adversarial tests
python3 -m unittest discover -v -s tests -t . -p "test_*.py"

# Run performance benchmarks
python3 benchmark.py
```

---

## License

LiteMigrate is open-source software licensed under the [Apache License, Version 2.0](LICENSE).
