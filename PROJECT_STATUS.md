# LiteMigrate — Project Status & Inventory Assessment

**Date:** November 10, 2026  
**Status:** Alpha / Pre-Release Candidate (Engineering Reconciliation Phase)  
**Workspace Root:** `/Users/chiragjangir/Desktop/litemigrate`  
**Host Environment:** macOS (Darwin 24.3.0, Apple Silicon arm64), Python 3.11+ / SQLite 3.53.4

---

## 1. Project Overview & Artifact Inventory

LiteMigrate is an open-source, local-first safety tool for SQLite database migrations. It verifies migrations in an isolated shadow database before applying them to production, preventing silent data corruption, cascade wipes, and concurrent write collisions.

### Artifact Inventory & Locations

| Component / Artifact | Current Location | Preserved Status | Description |
| :--- | :--- | :--- | :--- |
| **Phase 3 Baseline & Phase 5 Engine** | `phase3_backup/prototype_shadow_migrate.py` | Preserved read-only in `phase3_backup/` | 1,288-line single-file prototype containing Phase 5 remediations |
| **Phase 4 Audit Report** | `phase3_backup/independent_audit_report.md` | Preserved read-only | Details 14 adversarial findings (4 Critical, 5 High, 5 Med/Low) |
| **Phase 4 Validation Report** | `phase3_backup/validation_report.md` | Preserved read-only | Initial baseline validation report |
| **Phase 5 Remediation Report** | `phase3_backup/remediation_report.md` | Preserved read-only | Summary of fixes for findings C-01..C-04, D-01..D-04, S-01..S-04, P-01..P-02 |
| **Phase 5 Architecture Spec** | `phase3_backup/updated_architecture.md` | Preserved read-only | 6-stage lifecycle architecture and subsystem designs |
| **Phase 5 Concurrency Spec** | `phase3_backup/concurrency_guarantees.md` | Preserved read-only | Pager lock protocols, CAS verification, and limitation boundaries |
| **Phase 5 Security Review** | `phase3_backup/security_review.md` | Preserved read-only | Symlink mitigation, file modes (`0o600`), and untrusted schema enforcement |
| **Phase 5 Regression Results** | `phase3_backup/regression_test_results.md` | Preserved read-only | 38-test specification across 4 test suites |
| **Phase 5 Updated Validation** | `phase3_backup/updated_validation_report.md` | Preserved read-only | Post-remediation status report |

---

## 2. Existing Functionality vs. Verified Limitations

### Verified Existing Functionality
1. **Isolated Shadow Cloning:**
   - Universal fallback using `_bounded_sqlite_backup()` with monotonic deadline.
   - Linux `FICLONE` (`ioctl 0x40049409`) copy-on-write reflink cloning on supported filesystems (XFS/Btrfs).
   - macOS `clonefile(2)` via Darwin libc `CLONE_NOFOLLOW` (empirically verified on Apple Silicon APFS).
2. **Schema & Object Auditing:**
   - Captures `sqlite_master` non-table schema objects (`INDEX`, `TRIGGER`, `VIEW`).
   - Normalizes SQL DDL and detects unexpected dropped schema objects.
3. **Database Integrity & Foreign Key Enforcements:**
   - Runs `PRAGMA foreign_key_check` and `PRAGMA quick_check` / `integrity_check`.
   - Strictly enforces `PRAGMA trusted_schema = OFF` across all connections.
4. **Advisory Locking & WAL Hygiene:**
   - Advisory file locks (`fcntl.flock(LOCK_EX | LOCK_NB)`) on `<db>.litemigrate.lock`.
   - Cleans up ephemeral `-wal` and `-shm` sidecars on shadow databases.

---

## 3. Verified Engineering Gaps (Pre-Productization)

1. **Callable Migration Partial Execution Risk:**
   `_promote_shadow_to_source()` committed the source transaction prior to executing callable migrations. Callable migrations are non-atomic under this design and must be explicitly rejected in the public API for the MVP.
2. **Data Fingerprinting Missing Row Identity:**
   `_fingerprint_table_and_columns()` computed column hashes without incorporating canonical row identity or primary keys, allowing potential row-identity swap vulnerabilities. Must be fixed for rowid and `WITHOUT ROWID` tables with deterministic ordering.
3. **Documentation-Implementation Discrepancy (C API):**
   Reports claimed pointer extraction from CPython internal structs, but the actual implementation cleanly opened database handles via `sqlite3_open_v2` file paths. Documentation must honestly reflect the file-path implementation.
4. **Monolithic Prototype Packaging:**
   The codebase is currently a single prototype script without packaging metadata, standard modular structure, or CLI entrypoint.

---

## 4. Git & Repository Status

- **Working Directory:** `/Users/chiragjangir/Desktop/litemigrate`
- **Git Repository:** Not yet initialized (will be initialized as a clean, professional git repository during Milestone 5).
- **Existing Commits / Branches:** None.
- **GitHub Account:** `@chiragjangiir` authenticated via GitHub CLI (`gh`).
