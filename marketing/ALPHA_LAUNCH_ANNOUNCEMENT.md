# Announcing LiteMigrate v0.1.0-alpha.1: Safer SQLite Migrations Through Shadow Verification

**Release**: `v0.1.0-alpha.1` (Experimental Alpha)  
**Repository**: [https://github.com/chiragjangiir/litemigrate](https://github.com/chiragjangiir/litemigrate)  
**License**: Apache-2.0  
**Platform**: macOS, Linux, Windows | Python 3.9+ | SQLite 3.35+  

---

## The SQLite Migration Dilemma

SQLite powers millions of production backends, edge functions, and local-first applications. Yet running schema migrations on SQLite remains surprisingly treacherous.

Unlike database systems with rich DDL capabilities, SQLite often requires the **12-step table rebuild procedure** to modify tables:
1. Create a new table with the altered schema.
2. Copy rows from the old table using `INSERT INTO ... SELECT`.
3. Drop the old table.
4. Rename the new table.

If you make a minor mistake in this sequence—omitting a column from the `SELECT` list, altering column type affinities inadvertently, or failing to account for foreign key cascade actions—**SQLite will execute your migration with exit code 0 while silently truncating data or wiping related tables.**

Your migration tool reports "Success," but your database has lost data.

---

## Enter LiteMigrate: Test Before You Migrate

**LiteMigrate** is a local-first safety utility and Python library designed to eliminate silent migration failures.

Instead of running a migration directly against your active database file, LiteMigrate follows a **shadow verification workflow**:

```
[ Active Source Database ]
           │
           ▼ (Copy-on-write reflink: < 1 ms)
[ Isolated Shadow Copy ]
           │
           ├─► 1. Snapshot Schema & Row Fingerprints
           ├─► 2. Execute Migration SQL
           ├─► 3. Audit Relational Invariants (PRAGMA foreign_key_check)
           ├─► 4. Audit Physical Storage (PRAGMA integrity_check)
           ├─► 5. Enforce Policy (Block undeclared drops or row losses)
           │
           ▼
     [ Verdict ]
     ├── PASSED ──► Optional Safe Promotion (Atomic Backup + CAS Check)
     └── BLOCKED ─► Shadow discarded. Source database remains untouched.
```

---

## What Makes LiteMigrate Different?

### 1. Sub-Millisecond Shadow Sandboxing
Using modern filesystem copy-on-write reflinks (macOS APFS `clonefile`, Linux `ioctl(FICLONE)` on Btrfs/XFS), creating an isolated shadow database takes less than **1 millisecond**, even on multi-gigabyte files. For standard filesystems or databases with active uncheckpointed WAL frames, LiteMigrate falls back seamlessly to the transactional SQLite Online Backup API.

### 2. Multi-Invariant Auditing
LiteMigrate doesn't just check if SQLite exited cleanly. It audits:
- **Foreign Key Constraints**: Runs `PRAGMA foreign_key_check` to detect orphaned child rows.
- **Physical Page Health**: Executes `PRAGMA integrity_check` on the migrated shadow.
- **Streaming Row Fingerprints**: Verifies that existing rows were not silently modified, corrupted, or swapped.
- **Schema Object Tracking**: Verifies views, triggers, and indexes are preserved.

### 3. Concurrency-Safe Promotion (Compare-And-Swap)
When you choose to promote a validated migration (`litemigrate apply --confirm`), LiteMigrate acquires SQLite's write reservation (`BEGIN IMMEDIATE`) and inspects `PRAGMA data_version` and schema cookies. If another process wrote to the database while validation took place, promotion immediately aborts, preventing lost updates.

### 4. Zero Cloud, Zero Telemetry
LiteMigrate is local-first. The tool itself makes zero network calls and collects zero telemetry. Your schemas and data never leave your local machine.

---

## Getting Started in 3 Steps

### 1. Install the Alpha Wheel
```bash
python3 -m venv .venv
source .venv/bin/activate
curl -sLO https://github.com/chiragjangiir/litemigrate/releases/download/v0.1.0-alpha.1/litemigrate-0.1.0a1-py3-none-any.whl
pip install litemigrate-0.1.0a1-py3-none-any.whl
```

### 2. Validate a Migration Without Touching Your Database
```bash
litemigrate validate --db ./app.db --migration ./migrations/001_add_index.sql
```

### 3. Apply with Pre-Promotion Backup
```bash
litemigrate apply --db ./app.db --migration ./migrations/001_add_index.sql --confirm
```

---

## Experimental Alpha Status & Call for Testers

`v0.1.0-alpha.1` is an experimental pre-release intended for community verification. We invite developers and database practitioners to test LiteMigrate on **disposable SQLite databases** and report edge cases.

- **GitHub Repository**: [https://github.com/chiragjangiir/litemigrate](https://github.com/chiragjangiir/litemigrate)
- **Tester Quickstart**: [docs/TESTER_QUICKSTART.md](https://github.com/chiragjangiir/litemigrate/blob/main/docs/TESTER_QUICKSTART.md)
- **Report an Issue**: [GitHub Issue Templates](https://github.com/chiragjangiir/litemigrate/issues/new/choose)

*Note: LiteMigrate is not yet published to PyPI. Do not use this Alpha release on production databases without independent backups.*

