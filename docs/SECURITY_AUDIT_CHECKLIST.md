# Production SQLite Migration Security & Safety Checklist

This checklist defines mandatory operational standards before, during, and after executing schema migrations on mission-critical SQLite deployments using LiteMigrate.

---

## 1. Pre-Migration Environmental Controls

- [ ] **WAL Mode Active**: Ensure `PRAGMA journal_mode=WAL;` is enabled. WAL mode minimizes table lock contention and isolates readers from schema-modifying writers.
- [ ] **Foreign Key Enforcement**: Confirm `PRAGMA foreign_keys=ON;` is active on all connecting sessions.
- [ ] **Backup Isolation**: Verify an automated snapshot or file clone of the source database exists in a dedicated immutable backup location.
- [ ] **Filesystem Permissions**: The operating system process executing `litemigrate` must have read/write access to both the target database directory and the OS temporary directory (`/tmp` or `$TMPDIR`).
- [ ] **Free Disk Headroom**: Ensure filesystem free space is at least **2.5x the database file size** (to accommodate shadow database clone, write-ahead log, and potential table copy operations).

---

## 2. Shadow Validation Phase

- [ ] **Dry-Run Execution**: Run `litemigrate validate --db <path> --migration <file>` prior to touching production.
- [ ] **Schema Invariant Verification**: Confirm zero unintended column drops or data type mutations were detected.
- [ ] **Referential Integrity Audit**: Confirm `PRAGMA foreign_key_check` returned zero orphaned child rows.
- [ ] **Data Fingerprint Verification**: Verify row counts and primary key sets remain unchanged across existing unmutated tables.
- [ ] **Integrity Pragma**: Confirm `PRAGMA quick_check` and `PRAGMA integrity_check` both return `ok`.

---

## 3. Concurrency & Promotion Guardrails

- [ ] **Source Modification Check**: LiteMigrate verifies that the SHA256 checksum and WAL frame count of the source database match the pre-validation snapshot.
- [ ] **Lock Acquisition Timeout**: Apply operations must acquire an `EXCLUSIVE` lock within the configured `--timeout` window (default 10s) or gracefully abort.
- [ ] **Pre-Promotion Backup**: An automatic timestamped backup (`<dbname>.backup.<timestamp>.sqlite`) is written immediately prior to promotion.
- [ ] **Atomic Promotion**: The verified shadow database is promoted to source using atomic rename (`os.replace`) to ensure zero intermediate corruption.

---

## 4. Post-Migration Verification

- [ ] **Service Health**: Query core application health endpoints to verify connectivity.
- [ ] **Log Inspection**: Inspect application error logs for `sqlite3.OperationalError` or `database is locked`.
- [ ] **WAL Checkpoint**: Issue `PRAGMA wal_checkpoint(TRUNCATE);` during low-traffic maintenance window to flush WAL frames into main database file.
