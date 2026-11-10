# LiteMigrate

> **Safer SQLite migrations through shadow verification.**

LiteMigrate is an open-source, local-first safety utility for SQLite database migrations. It verifies migrations in an isolated shadow copy before touching production, checking for accidental row losses, silent data mutations, cascade wipes, broken foreign keys, and structural corruption.

[![CI Tests](https://github.com/chiragjangiir/litemigrate/actions/workflows/tests.yml/badge.svg)](https://github.com/chiragjangiir/litemigrate/actions/workflows/tests.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: Alpha](https://img.shields.io/badge/Status-Alpha_RC1-orange.svg)](PROJECT_STATUS.md)

---

## The Problem

SQLite is widely used in production web backends, edge nodes, mobile applications, and embedded systems. However, schema migrations in SQLite are prone to silent, irreversible failure modes:

1. **Foreign Key Cascade Wipes ([ariga/atlas #3317](https://github.com/ariga/atlas/issues/3317)):** When rebuilding a table with `foreign_keys=ON`, issuing `DROP TABLE parent` triggers `ON DELETE CASCADE` and wipes every child row in the database without any warning or syntax error.
2. **Column Alteration Blind Spots:** Adding a column while inadvertently mutating or zeroing out existing columns in the same migration script often passes standard migration tools unnoticed.
3. **Lost Updates Under Concurrency:** Applying a migration to a live database while concurrent transactions commit can lead to lost updates or corrupted WAL frames if the migration tool does not enforce strict writer locks and compare-and-swap (CAS) verification.
4. **Trigger and View Silencing:** Dropping or renaming a table can leave surviving triggers or views referencing invalid identifiers, which crash queries later during runtime.

Most migration tools report success as long as the SQL engine executes without an exception. **LiteMigrate checks whether your data actually survived.**

---

## How It Works

LiteMigrate validates migrations through a 6-stage verification lifecycle:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Security & Pre-flight Inspection                                    │
│    • Rejects symlinks on source, shadow, lock, and WAL files.          │
│    • Allocates an isolated 0o700 temporary workspace.                  │
│    • Enforces PRAGMA trusted_schema = OFF on all connections.          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. Consistent Shadow Database Creation                                 │
│    • Active WAL: Bounded libsqlite3 Backup API with deadline.          │
│    • Quiescent DB: macOS APFS clonefile(2) or Linux FICLONE ioctl.     │
│    • Mode 0o600 enforced across all copy-on-write copies.              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. Baseline Snapshot (from isolated shadow copy)                       │
│    • Canonical logical digest of sqlite_master and table contents.     │
│    • Table row counts, content hashes, and per-column digests.         │
│    • Non-table schema cataloging (indexes, triggers, views).           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. Transactional Shadow Migration Execution                            │
│    • Splits SQL into complete statements via SQLite's C lexer.         │
│    • Executes inside explicit BEGIN ... COMMIT on shadow copy.         │
│    • Source database remains 100% untouched.                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. Multi-Invariant Shadow Audit                                        │
│    • PRAGMA foreign_key_check run before integrity checks.             │
│    • PRAGMA integrity_check verifies structural B-tree health.         │
│    • Checks for unexpected drops, row losses, and shared-column edits. │
│    • Verifies surviving views parse and execute.                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 6. Zero-TOCTOU Atomic Promotion (apply --confirm)                      │
│    • Acquires advisory flock on <source>.litemigrate.lock.             │
│    • Creates 0o600 pre-promotion rollback backup.                      │
│    • Acquires BEGIN IMMEDIATE on source connection.                    │
│    • In-transaction CAS: source live digest == shadow baseline digest. │
│    • Replays SQL inside held lock, verifies FKs, and COMMITs.          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Installation

LiteMigrate is local-first with **zero mandatory external dependencies** outside Python's standard library and the platform's SQLite C library (`libsqlite3`).

```bash
git clone https://github.com/chiragjangir/litemigrate.git
cd litemigrate
python3 -m pip install -e .
```

Requires **Python 3.9+** and **SQLite 3.35+**.

---

## Quick-Start Example

```bash
# 1. Inspect the database schema and integrity
litemigrate inspect --db ./app.db

# 2. Test your migration against an isolated shadow database
litemigrate validate --db ./app.db --migration ./migrations/001_add_index.sql

# 3. Apply the migration safely with explicit confirmation
litemigrate apply --db ./app.db --migration ./migrations/001_add_index.sql --confirm
```

---

## CLI Reference

### `litemigrate inspect`
Displays database path, SQLite version, journal mode, size, table count, schema object count, and basic database integrity status. Never displays sensitive row contents.

```bash
litemigrate inspect --db ./app.db [--json]
```

### `litemigrate validate`
Creates an isolated shadow database, runs the migration on the shadow copy, audits all invariants, and outputs a structured audit report. **Never modifies the source database.**

```bash
litemigrate validate --db ./app.db --migration ./001_migration.sql [--policy ./policy.json] [--json]
```

### `litemigrate apply`
Validates on the shadow database first, requires explicit user confirmation, creates a recoverable `0o600` backup, verifies the source has not changed concurrently under an exclusive writer lease, and atomically commits the migration.

```bash
litemigrate apply --db ./app.db --migration ./001_migration.sql --confirm [--policy ./policy.json] [--json]
```

### `litemigrate report`
Reads and formats a previously generated JSON audit report.

```bash
litemigrate report --input ./audit-report.json [--json]
```

---

## Safety Model & Policy

By default, LiteMigrate operates under strict conservative defaults:
- **No table drops** permitted without declaration in `allowed_dropped_tables`.
- **No row losses** permitted without declaration in `allowed_row_loss_tables`.
- **No column or row data mutations** permitted without declaration in `allowed_mutated_tables`.
- **No dropped views, triggers, or indexes** permitted without explicit allowlisting.

When performing intentional deletions or alterations, pass an explicit JSON policy:

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

### Verdict Exit Codes

| Exit Code | Verdict Category | Description |
| :---: | :--- | :--- |
| **`0`** | `PASSED` | Validation and/or application completed successfully. |
| **`1`** | `BLOCKED_*` | Migration blocked by safety audit (unexpected drop, row loss, mutation, FK violation). |
| **`2`** | `BLOCKED_CONCURRENT_*` | Concurrent writer conflict detected or lock deadline exceeded. |
| **`3`** | `Security Error` | Symlink detected, permissions invalid, or path safety failure. |
| **`4`** | `Aborted / Unconfirmed` | Apply command ran without `--confirm` in non-interactive shell. |
| **`5`** | `Execution Error` | Migration SQL execution exception or file error. |

---

## What LiteMigrate Verifies (And What It Cannot Prove)

### LiteMigrate Verifies:
- **Foreign Key Consistency:** `PRAGMA foreign_key_check` is executed on the shadow copy after migration and re-verified on the source before commit.
- **Data Preservation:** Unintended row losses and silent modifications to existing columns are detected via row-identity-bound streaming SHA-256 hashes.
- **Concurrent Writer Isolation:** External transactions committed by cooperating SQLite processes while validation is running are detected via an in-transaction CAS check, rolling back promotion to preserve external writes.
- **B-Tree Structural Health:** `PRAGMA integrity_check` and `PRAGMA quick_check` run on the shadow database.

### What LiteMigrate Cannot Prove:
- **Non-SQLite Rogue Writers:** If an external process writes raw bytes directly into the `.db` file descriptor bypassing SQLite's locking protocol, OS-level filesystem corruption cannot be prevented.
- **Application Query Semantics:** LiteMigrate verifies relational data and schema integrity; it cannot verify that your application's ORM queries remain logically compatible with the new schema.
- **Arbitrary Python Callables:** Public API strictly supports SQL script migrations. Python callables are excluded because they cannot be guaranteed atomic under SQLite transaction boundaries.

---

## Supported Environments & Benchmarks

| Platform | Filesystem | Shadow Clone Mechanism | Verification Status |
| :--- | :--- | :--- | :--- |
| **macOS (Darwin)** | Apple APFS | `clonefile(2)` via Darwin libc | **Verified on Apple Silicon APFS** |
| **Linux (x86_64 / arm64)** | XFS / Btrfs | `ioctl(..., FICLONE)` | **Verified on Linux 6.x XFS** |
| **Universal POSIX** | Ext4, ZFS, tmpfs, etc. | `sqlite3_backup_*` C API | **Verified Universal Fallback** |

### Empirically Measured Benchmarks

Measured on macOS Darwin (Apple Silicon, APFS volume) using `benchmark.py`:

| Database Scale | Clone Strategy | Clone Duration | Isolated Peak RSS |
| :--- | :--- | :--- | :--- |
| **5.0 MB** | `APFS_CLONEFILE` (CoW) | **1.21 ms** | **26.05 MB** |
| **5.0 MB** | `SQLITE_BACKUP_API` | 18.99 ms | 37.27 MB |
| **25.0 MB** | `APFS_CLONEFILE` (CoW) | **1.18 ms** (~111x faster) | **25.91 MB** |
| **25.0 MB** | `SQLITE_BACKUP_API` | 131.37 ms | 61.88 MB |

---

## Running the Test Suite

LiteMigrate includes a comprehensive 59-test automated regression suite covering unit, integration, and adversarial concurrency scenarios:

```bash
# Run complete test suite
python3 -m unittest discover -v -s tests -t . -p "test_*.py"

# Run performance benchmarks
python3 benchmark.py
```

---

## Project Status & Roadmap

LiteMigrate is currently **Alpha (Release Candidate 1)**.

- [x] Phase 1: Problem identification & empirical verification.
- [x] Phase 2: Copy-on-write clone engines (APFS and Linux FICLONE).
- [x] Phase 3: Adversarial audit and remediation of 14 core defects.
- [x] Phase 4: Resolution of callable migration and canonical row identity gaps.
- [x] Phase 5: Python package structure and command-line interface.
- [ ] Phase 6: Automated schema reverse-engineering & visual migration diffs.
- [ ] Phase 7: GitHub Action for CI/CD pre-merge migration validation.

---

## License

LiteMigrate is open-source software licensed under the [Apache License, Version 2.0](LICENSE).
