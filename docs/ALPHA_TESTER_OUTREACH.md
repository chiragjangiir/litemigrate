# LiteMigrate — Alpha Tester Outreach & Invitation Guide

This document contains targeted, respectful outreach messages for inviting experienced database engineers, Python developers, and systems practitioners to test **LiteMigrate `v0.1.0-alpha.1`**.

---

## Outreach Principles & Code of Conduct

1. **Strictly Non-Promotional**: We are seeking technical feedback, edge cases, and safety verification, not hype, stars, or artificial engagement.
2. **Never Spam**: Do not post duplicate messages, tag individuals without context, or mass-message community channels.
3. **Transparent Prerelease Disclosure**: Always disclose that `v0.1.0-alpha.1` is an experimental Alpha.
4. **Mandatory Disposable Data Warning**: Always remind testers to test only on disposable synthetic databases.
5. **No Claims of Endorsement**: Never claim endorsement by SQLite, Python, or external organizations.

---

## 1. Message Template: Python Developer Communities (r/Python, Python Discord, Discourse)

**Subject / Title**: LiteMigrate (Alpha): Testing SQLite migrations against isolated copy-on-write shadow copies before promotion

```markdown
Hi everyone,

I've been working on an open-source project called **LiteMigrate** to address a common pitfall in SQLite migrations: in SQLite, a migration script can execute with exit code 0 while still silently dropping columns or wiping child rows via foreign key cascade deletions.

LiteMigrate is a local-first safety utility that tests migrations in a sandbox before touching your database:

1. **Sub-millisecond shadow cloning**: Uses filesystem copy-on-write reflinks (APFS on macOS, FICLONE on Linux) or the SQLite Online Backup API to create an isolated sandbox in < 1 ms.
2. **Invariant validation**: Runs the migration on the shadow copy, checking schema diffs, streaming row fingerprints, foreign keys (`PRAGMA foreign_key_check`), and page integrity (`PRAGMA integrity_check`).
3. **Safe promotion**: When applying, it creates a timestamped pre-promotion backup (`.bak`), acquires an exclusive writer lock (`BEGIN IMMEDIATE`), verifies `PRAGMA data_version` to catch concurrent writes, and applies the migration.

We just published our first experimental Alpha release (`v0.1.0-alpha.1`).

We are looking for feedback from developers on:
- How it handles unusual SQLite schemas (WITHOUT ROWID, STRICT mode, composite keys, non-ASCII column names).
- CLI ergonomics and report clarity.
- Platform behavior across different Linux distributions and filesystems.

**Important safety note**: LiteMigrate Alpha is experimental. Please test exclusively on disposable, non-production databases.

- Repository: https://github.com/chiragjangiir/litemigrate
- Alpha Release: https://github.com/chiragjangiir/litemigrate/releases/tag/v0.1.0-alpha.1
- Tester Quickstart: https://github.com/chiragjangiir/litemigrate/blob/main/docs/TESTER_QUICKSTART.md

Any feedback, edge cases, or bug reports are warmly welcome!
```

---

## 2. Message Template: SQLite & Database Specialists (SQLite Forum, r/sqlite)

**Subject / Title**: Feedback requested: LiteMigrate — pre-promotion shadow verification and CAS concurrency detection for SQLite

```markdown
Hello SQLite community,

We have released an experimental open-source tool, **LiteMigrate** (`v0.1.0-alpha.1`), aimed at preventing accidental data loss during SQLite schema migrations.

When executing DDL or multi-step 12-step table rebuilds, subtle issues (such as temporary foreign key deactivation without full post-migration re-checking, or uncheckpointed WAL frames) can cause corruption or orphan records.

LiteMigrate implements:
- Copy-on-write shadow creation (APFS `clonefile`, Linux `ioctl(FICLONE)`, with transactional fallback to `sqlite3_backup_*`).
- Pre- and post-migration schema and row hashing (including IEEE-754 signed zero float discrimination and column name aliasing safety for `rowid`/`_rowid_`/`oid`).
- Enforced `PRAGMA trusted_schema = OFF;` on all opened connections.
- Concurrency detection before promotion using SQLite `PRAGMA data_version` and schema cookies under `BEGIN IMMEDIATE`.

We would love technical review from SQLite internals specialists on:
- Our concurrency locking and promotion invariants (`litemigrate/promotion.py`).
- Our row-identity and composite key hashing strategy (`litemigrate/fingerprint.py`).
- Edge cases in SQLite virtual tables or triggers during shadow cloning.

Code and documentation:
https://github.com/chiragjangiir/litemigrate

Feedback can be submitted directly via GitHub issues or in this thread.
```

---

## 3. Message Template: Backend & Platform Engineers (Hacker News "Show HN", DevOps / Platform Discord)

**Title**: Show HN: LiteMigrate (Alpha) – Test SQLite migrations on shadow copies before promotion

```markdown
LiteMigrate is an open-source, local-first utility designed to make SQLite migrations safer by validating them against an isolated copy-on-write shadow database before promotion.

Why we built it:
Most migration tools only check whether SQL executes without syntax errors. In SQLite, a flawed table rebuild or cascade delete can execute with exit code 0 while silently deleting child records or truncating data.

How it works:
- Clones your SQLite database using copy-on-write reflinks (APFS clonefile or Linux FICLONE) in under 1 ms.
- Executes migration SQL strictly inside the shadow copy.
- Audits schema diffs, row fingerprints, foreign keys (`PRAGMA foreign_key_check`), and page integrity (`PRAGMA integrity_check`).
- On `apply`, acquires an exclusive writer lock (`BEGIN IMMEDIATE`), verifies `PRAGMA data_version` hasn't changed (Compare-And-Swap), creates a pre-promotion backup, and commits changes.
- Generates a machine-readable JSON audit report suitable for CI/CD gates.

We've published `v0.1.0-alpha.1` as an experimental Alpha. It is 100% local-first: zero cloud dependencies, zero telemetry, and zero data uploads.

Repo: https://github.com/chiragjangiir/litemigrate
Docs: https://github.com/chiragjangiir/litemigrate/blob/main/README.md

We'd love feedback on CLI usability, failure modes, and compatibility across Linux filesystems (ext4, XFS, ZFS, Btrfs). Please test with disposable databases only!
```
