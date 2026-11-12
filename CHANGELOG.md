# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- The CLI now returns the documented exit codes instead of reporting an unexpected failure: `SecurityError` exits 3, and `LockTimeoutError` / `ConcurrencyConflictError` exit 2 (previously all three exited 5).

## [0.1.0-alpha.1] - 2026-11-10

### Added
- **Core Engine & Architecture:**
  - Local-first shadow verification engine for SQLite migrations.
  - Zero-TOCTOU promotion protocol with persistent writer leases and atomic in-transaction CAS verification.
  - Streaming row-identity-bound fingerprinting for standard `rowid` and `WITHOUT ROWID` primary key tables.
  - Multi-invariant auditing: detection of dropped tables, row losses, per-column silent mutations, dropped schema objects (views, triggers, indexes), foreign key violations, and B-tree integrity corruption.
- **Cloning & Platform Support:**
  - macOS Darwin native APFS `clonefile(2)` copy-on-write cloning verified on Apple Silicon.
  - Linux `FICLONE` (`ioctl 0x40049409`) copy-on-write reflink cloning on XFS/Btrfs.
  - Universal bounded SQLite Backup API fallback directly binding `libsqlite3` C API with monotonic deadlines.
- **Security & Hardening:**
  - Mandatory `PRAGMA trusted_schema = OFF;` verification across all database connections.
  - Strict symlink traversal rejection (`is_symlink()` and `O_NOFOLLOW`).
  - Private workspace isolation (`0o700` directories) and strict file mode enforcement (`0o600`).
  - Robust handling of user columns shadowing physical SQLite rowid aliases (`rowid`, `_rowid_`, `oid`).
  - Safe multi-line SQL path resolution preventing OS `stat()` string overflows (`ENAMETOOLONG`).
- **Command-Line Interface (CLI):**
  - `litemigrate inspect`: Inspect schema, journal mode, table counts, and database integrity.
  - `litemigrate validate`: Test migration against an isolated shadow copy without modifying source.
  - `litemigrate apply`: Enforce explicit confirmation, create pre-promotion rollback backup, verify CAS, and promote safely.
  - `litemigrate report`: Display and format previously generated JSON audit reports.
- **Documentation & Verification:**
  - Comprehensive documentation: architecture, safety model, concurrency protocol, limitations, and benchmark methodology.
  - Automated test suite with 62 passing tests across unit, integration, and adversarial suites.
  - GitHub Actions CI matrix running across Ubuntu Linux and macOS Darwin on Python 3.9, 3.10, 3.11, and 3.12.
