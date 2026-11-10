# LiteMigrate — Known Limitations & Operational Boundaries

This document provides transparent technical documentation of LiteMigrate's architectural boundaries, platform-specific behaviors, and operational limits as of **v0.1.0-alpha.1**.

---

## 1. Scope & Database Engines

- **SQLite Only:** LiteMigrate is intentionally engineered for SQLite (v3.35.0+ recommended). It does not support PostgreSQL, MySQL, DuckDB, or LibSQL.
- **Pure SQL Migrations:** Only SQL migration scripts (`.sql` files or SQL statement strings) are accepted. Python callable functions are explicitly rejected because multi-statement callables cannot be rolled back atomically in external processes without custom write-ahead coordination.

---

## 2. Table Structure & Fingerprinting Boundaries

- **Tables Shadowing Rowid Without Primary Key:**
  In SQLite, if a user table defines columns explicitly named `rowid`, `_rowid_`, and `oid`, the internal 64-bit integer rowid becomes inaccessible. If such a table also lacks a declared `PRIMARY KEY`, LiteMigrate cannot establish a deterministic row identity and will reject the migration with `UnsupportedTableStructureError`.
- **WITHOUT ROWID Tables Without Primary Key:**
  SQLite disallows `WITHOUT ROWID` tables without a primary key by specification. If encountered, LiteMigrate rejects them.
- **Virtual Tables & FTS:**
  Full-Text Search (FTS3/4/5) and custom SQLite virtual tables with non-standard backing tables may produce warnings or require specific policy allowances if their underlying shadow tables are modified during rebuilds.

---

## 3. Concurrency & Locking Boundaries

- **SQLite-Cooperating Writers vs. Non-SQLite Writers:**
  - **Cooperating Writers:** LiteMigrate acquires a `BEGIN IMMEDIATE` writer lock during promotion and compares the pre-migration database digest against the current database state. If any SQLite connection committed a write between shadow snapshotting and promotion, LiteMigrate aborts immediately with `BLOCKED_SOURCE_MODIFIED_CONCURRENTLY`.
  - **Non-SQLite File Modification:** If an external process directly truncates, writes raw bytes, or deletes the `.db` file using raw OS filesystem calls (bypassing SQLite's file-locking and VFS protocol), POSIX filesystem semantics do not protect SQLite page cache consistency.
- **High-Write Environments:**
  In environments with non-stop concurrent database writes, acquiring the writer lock and passing the CAS barrier may require retries or scheduling migrations during lower-traffic windows.

---

## 4. Platform Reflink & Cloning Support

- **macOS:** LiteMigrate uses macOS `clonefile(2)` on APFS volumes. On non-APFS volumes (such as exFAT or FAT32 external drives), it automatically falls back to the transactional SQLite Online Backup API.
- **Linux:** LiteMigrate attempts copy-on-write via `ioctl(FICLONE)` on supported filesystems (Btrfs, XFS). On filesystems without reflink support (ext4), it automatically falls back to the SQLite Online Backup API.
- **Active WAL Frames:**
  If an active SQLite database is in WAL mode and contains uncheckpointed WAL frames, reflink cloning alone would omit unflushed frames in the `-wal` file. LiteMigrate detects active WAL frames and uses the SQLite Backup API to ensure transactional point-in-time consistency.

---

## 5. Security & Execution Boundaries

- **`PRAGMA trusted_schema`:**
  LiteMigrate forces `PRAGMA trusted_schema = OFF` on all opened connections to prevent malicious SQL expressions inside triggers or views from invoking arbitrary extension functions.
- **Symlinks:**
  Symlinks at source, destination, or backup targets are explicitly rejected before access to eliminate symlink redirection attacks.
