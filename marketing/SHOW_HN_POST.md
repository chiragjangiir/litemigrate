# Show HN Launch Package: LiteMigrate

This document contains two launch-ready versions of the **Show HN** post for LiteMigrate, along with title evaluations and posting guidelines.

> [!IMPORTANT]
> **DO NOT PUBLISH EXTERNALLY WITHOUT EXPLICIT APPROVAL.**
> These drafts are prepared for review only.

---

## Title Evaluation & Recommended Options

### Evaluated Options:
1. `Show HN: LiteMigrate – Validate SQLite migrations on a shadow database before promotion` *(Recommended)*
   - **Pros**: Direct, technically precise, uses standard database vocabulary ("shadow database", "promotion"). Immediately clear to backend/database engineers.
   - **Cons**: "Shadow database" might sound heavy to developers who don't know it's a sub-millisecond local clone.
2. `Show HN: LiteMigrate – Test SQLite migrations on an isolated shadow copy before promotion`
   - **Alternative**: Slightly softer ("shadow copy" rather than "shadow database"), emphasizes isolation.
3. `Show HN: LiteMigrate – Local-first safety tool to test SQLite migrations in a sandbox`
   - **Alternative**: More consumer-friendly, but "sandbox" can imply containerization (Docker, WASM) rather than filesystem copy-on-write.

**Selected Title**:  
`Show HN: LiteMigrate – Validate SQLite migrations on a shadow database before promotion`

---

## Version 1: Short & Direct Show HN Post (Recommended)

```markdown
Hi HN,

I built LiteMigrate, a local-first CLI tool and Python library to make SQLite migrations safer.

The problem:
In SQLite, running migrations directly against your live database is surprisingly risky. Because SQLite has limited ALTER TABLE capabilities, complex schema changes often require the 12-step table rebuild procedure (create temp table, copy data, drop old table, rename). If a developer accidentally omits a column in the SELECT query, or if an ON DELETE CASCADE constraint triggers unexpectedly, SQLite will execute the script with exit code 0 while silently truncating data or wiping related tables.

What LiteMigrate does:
Instead of running migrations on the live database, LiteMigrate validates them against an isolated "shadow" copy first:

1. Shadow Cloning: On macOS (APFS clonefile) and Linux (FICLONE reflink), it creates a copy-on-write clone of the SQLite file in under 1 ms without duplicating physical disk blocks. On other systems or active WAL files with uncheckpointed frames, it uses the SQLite Online Backup API.
2. Multi-Invariant Audit: It executes the migration SQL strictly inside the shadow copy and runs checks:
   - PRAGMA foreign_key_check to catch orphaned rows.
   - PRAGMA integrity_check to detect physical page corruption.
   - Streaming row fingerprinting (using IEEE-754 signed zero discrimination and rowid aliasing safety) to ensure existing data wasn't silently altered or dropped.
   - Policy enforcement: table drops and row losses are blocked by default unless declared in an explicit policy.json.
3. Concurrency-Safe Promotion: When you run `litemigrate apply --confirm`, it acquires SQLite's write reservation (`BEGIN IMMEDIATE`), checks `PRAGMA data_version` and schema cookies to ensure no concurrent SQLite process wrote to the database while validation was running (Compare-And-Swap), creates an atomic timestamped backup (.bak), and applies the changes.

Status:
This is an experimental Alpha (v0.1.0-alpha.1). It is local-first: zero cloud services, zero telemetry, and the tool itself makes zero network calls. We have an 80-test automated suite running across Python 3.9–3.12 on macOS and Linux, but we have not published to PyPI yet.

GitHub: https://github.com/chiragjangiir/litemigrate
Alpha Release: https://github.com/chiragjangiir/litemigrate/releases/tag/v0.1.0-alpha.1
Quickstart Guide: https://github.com/chiragjangiir/litemigrate/blob/main/docs/TESTER_QUICKSTART.md

I would love technical criticism and feedback from database specialists, Python developers, and systems engineers. In particular:
- How does the concurrency/promotion logic hold up in your SQLite workloads?
- What edge cases exist in your schemas (e.g. WITHOUT ROWID, STRICT mode, custom triggers, virtual tables) that might trip up row fingerprinting?

Please test on disposable databases only!
```

---

## Version 2: Detailed Technical Show HN Post (Long Form / First Comment)

```markdown
Hi HN,

I'm sharing LiteMigrate, an open-source, local-first safety utility and Python library for SQLite migrations.

### The Background
Most database migration tools answer: "Did SQLite execute the SQL without raising a syntax error?"

In SQLite, that answer is not enough. Common failure modes:
1. Foreign Key Cascades: Dropping a parent table or running an unchecked DELETE can silently wipe thousands of child rows across unrelated tables without raising an error.
2. 12-Step Rebuild Truncation: Because SQLite cannot alter column types or add certain constraints directly, tools rewrite tables via `INSERT INTO new SELECT ... FROM old`. Omitting a column from the SELECT list drops that column and its data permanently while reporting exit code 0.
3. Dynamic Type Corruption: SQLite allows storing text in integer columns unless STRICT tables are used, leading to subtle data loss during reshaping queries.
4. Concurrent Lost Updates: If a migration takes a few seconds and another process writes to the database, traditional runners can overwrite or conflict with that data.

### How LiteMigrate Works
LiteMigrate enforces a "Test before you migrate. Validate first. Promote safely" workflow:

1. Fast Copy-on-Write Sandboxing:
Creating an isolated copy of a database is traditionally slow. LiteMigrate uses OS-level copy-on-write reflinks:
- macOS: `clonefile(2)` via APFS (< 0.5 ms).
- Linux: `ioctl(FICLONE)` on Btrfs and XFS (< 0.5 ms).
- Fallback / Active WAL: Uses the transactional SQLite Online Backup API (`sqlite3_backup_*`) if uncheckpointed WAL frames exist.

2. Isolated Multi-Invariant Auditing:
The migration executes strictly in the shadow copy:
- Page Integrity: Runs `PRAGMA integrity_check`.
- Relational Constraints: Runs `PRAGMA foreign_key_check` across all tables.
- Row-Level Continuity: Tracks streaming row hashes (in 1,000-row chunks) before and after migration to verify existing cell values were not swapped, mutated, or truncated.
- Destructive Policy: `DROP TABLE` or row loss is blocked by default unless authorized in an auditable `policy.json`.

3. Concurrency-Safe Promotion (CAS):
To prevent Time-of-Check to Time-of-Use (TOCTOU) issues during promotion:
- Acquires SQLite's write reservation (`BEGIN IMMEDIATE`) on the source database.
- Checks `PRAGMA data_version` and the schema cookie against baseline values to verify cooperating SQLite processes have not committed changes.
- If concurrent writers committed data during validation, it aborts immediately without touching the live database. (Note: this detects cooperating SQLite engine transactions; raw file overwrites bypassing SQLite are outside engine scope).
- If unchanged, it creates an atomic `.bak` file and applies the migration.

### A 30-Second Example
```bash
# Install Alpha wheel
curl -sLO https://github.com/chiragjangiir/litemigrate/releases/download/v0.1.0-alpha.1/litemigrate-0.1.0a1-py3-none-any.whl
pip install litemigrate-0.1.0a1-py3-none-any.whl

# Inspect schema
litemigrate inspect --db app.db

# Validate on shadow copy (app.db remains untouched)
litemigrate validate --db app.db --migration migration.sql

# Apply with pre-promotion backup & CAS check
litemigrate apply --db app.db --migration migration.sql --confirm
```

### Current Status
LiteMigrate is currently at `v0.1.0-alpha.1` (experimental Alpha). It is single-node, SQL-only (arbitrary Python callables are intentionally rejected at the API boundary to preserve auditability), and SQLite-only.

Code & Architecture: https://github.com/chiragjangiir/litemigrate
Release Assets: https://github.com/chiragjangiir/litemigrate/releases/tag/v0.1.0-alpha.1

I welcome adversarial feedback, edge cases, and code reviews on our concurrency lease logic and row fingerprinting implementation.
```

