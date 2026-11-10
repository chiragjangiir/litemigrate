# LiteMigrate v0.1.0-alpha.1 — Release Notes

**Release:** `v0.1.0-alpha.1` (Experimental Alpha)  
**Date:** November 10, 2026  
**Commit:** `e32b11d`  
**License:** Apache-2.0  

---

> [!WARNING]
> **Experimental Alpha Release Notice:**  
> LiteMigrate `v0.1.0-alpha.1` is an early experimental release designed for developer evaluation, testing, and feedback. **Do not test or run migrations on the sole copy of important production databases.** Always maintain verified, independent off-site backups before applying schema changes to any live database.

---

## Overview

LiteMigrate is a local-first safety utility and CLI for SQLite database migrations. It verifies migrations inside an isolated copy-on-write shadow copy before touching production, checking for accidental row losses, silent column data modifications, foreign key cascade wipes, and B-tree corruption.

---

## Key Capabilities

- **Isolated Shadow Validation:** Tests SQL migrations against an isolated copy-on-write shadow database (using macOS APFS `clonefile` or Linux `FICLONE` where supported, with transactional SQLite Online Backup API fallback). **The source database is never modified during validation.**
- **Relational & Data Invariant Auditing:**
  - Detects foreign key cascade wipes ([ariga/atlas #3317](https://github.com/ariga/atlas/issues/3317)) where dropping a parent table deletes child records.
  - Detects unexpected row loss across all tables.
  - Detects silent data mutations on existing columns via row-identity-bound streaming SHA-256 fingerprinting.
  - Verifies surviving views and triggers remain parseable and executable.
  - Runs `PRAGMA foreign_key_check` and `PRAGMA integrity_check`.
- **In-Transaction CAS Concurrency Protocol:** When promoting migrations (`apply --confirm`), LiteMigrate acquires an advisory lock (`<source>.litemigrate.lock`) and a `BEGIN IMMEDIATE` writer lock on the source connection. It re-computes the logical database digest inside the lock. If any cooperating SQLite writer modified the database since shadow creation, promotion aborts with `BLOCKED_SOURCE_MODIFIED_CONCURRENTLY` to prevent lost updates.
- **Pre-Promotion Rollback Backup:** Creates an automatic timestamped, owner-only (`0o600`) recovery backup (`<source>.pre_migrate_<nanoseconds>.bak`) before applying any migration to the live database.
- **Strict Security Defaults:** Mandatory `PRAGMA trusted_schema = OFF;`, strict symlink rejection on all database and lock paths, and private workspace directories (`0o700`).

---

## Operational Scope & Known Limitations

- **Experimental Status:** This is an initial Alpha release intended for testing on non-production or backed-up development databases.
- **Pure SQL Migrations Only:** Only SQL migration scripts are accepted. Python callable functions are explicitly rejected because multi-statement callables cannot be rolled back atomically under SQLite transaction boundaries.
- **SQLite Only:** Engineered strictly for SQLite (v3.35.0+). Other database engines (PostgreSQL, MySQL, DuckDB, LibSQL) are not supported.
- **Concurrency Boundary:** LiteMigrate's CAS barrier protects against concurrent writes from cooperating SQLite processes. It cannot protect against non-SQLite processes writing raw bytes directly to the underlying filesystem file descriptor.
- **Row Identity Requirements:** Supports standard rowid tables and `WITHOUT ROWID` tables with declared primary keys. Tables that shadow all rowid aliases (`rowid`, `_rowid_`, and `oid`) simultaneously without a primary key cannot be deterministically fingerprinted and are rejected.

---

## Verified Environments

- **macOS:** Darwin (Apple Silicon arm64, macOS 14/15/26) on APFS
- **Linux:** Ubuntu 22.04 / 24.04 (x86_64) on XFS / ext4
- **Python:** 3.9, 3.10, 3.11, 3.12
- **SQLite:** 3.37.2 through 3.53.4 (WAL and DELETE journal modes)
- **CI Test Suite:** 62 passing unit, integration, and adversarial tests across all 8 matrix configurations.

---

## Installation

From the release wheel:
```bash
python3 -m pip install litemigrate-0.1.0a1-py3-none-any.whl
```

Or from source:
```bash
git clone https://github.com/chiragjangiir/litemigrate.git
cd litemigrate
git checkout v0.1.0-alpha.1
python3 -m pip install -e .
```
