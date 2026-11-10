# LITEMIGRATE — PHASE 4 INDEPENDENT ADVERSARIAL ENGINEERING AUDIT REPORT

## 1. Executive Audit Verdict: **BLOCKED**

Following a line-by-line inspection of all seven Phase 3 files (`prototype_shadow_migrate.py`, `database_setup.py`, `test_shadow_migration.py`, `test_foreign_key_cascade.py`, `benchmark.py`, `README.md`, and `VALIDATION_REPORT.md`) and execution of a 12-test adversarial exploit suite (`test_adversarial_audit.py`), the Phase 3 prototype is assigned a formal engineering verdict of **BLOCKED**.

### Why the Verdict is `BLOCKED` (Despite 14/14 Phase 3 Tests Passing)
While the Phase 3 prototype successfully proved basic single-threaded shadow detection of `ON DELETE CASCADE` table rebuilds ([`ariga/atlas` Issue #3317](https://github.com/ariga/atlas/issues/3317)) and achieved `0.32–0.50 ms` Linux XFS `FICLONE` cloning, independent adversarial testing uncovered **4 Critical safety defects**, **5 High-severity defects**, and **5 Medium/Low defects** that violate core database reliability and security guarantees:

1. **Critical Defect `C-01` (Post-Clone / Pre-Digest TOCTOU Lost Update):** `create_shadow_database` acquires `BEGIN IMMEDIATE` and **immediately releases it via `ROLLBACK;` on line `302`** *before* cloning `source_db` and *before* `orig_digest_at_snapshot` is computed on line `450`. A concurrent writer that commits between line `396` (end of clone) and line `450` (digest calculation) has its transaction included in `orig_digest_at_snapshot` and `orig_digest_after_shadow`—bypassing the Compare-and-Swap check completely—and its **committed data is silently overwritten and permanently destroyed** during promotion!
2. **Critical Defect `C-02` (Post-CAS / Pre-Promotion TOCTOU Lost Update):** No database lock is held between the CAS digest check on line `617` and `_promote_shadow_to_source` on line `640`. Any transaction committed in that window is **silently overwritten** by `shadow_conn.backup(source_conn)`.
3. **Critical Defect `C-03` (`sqlite3.Connection.backup()` Infinite C-Level Hang):** In CPython's `_sqlite` module (`Modules/_sqlite/connection.c`), calling `.backup()` with the default `pages=-1` (lines `381` and `690`) enters an infinite C retry loop (`sqlite3_sleep`) whenever the target database is locked by a concurrent writer, **completely ignoring `PRAGMA busy_timeout`** and hanging the process forever.
4. **Critical Defect `D-01` (`ALTER TABLE ... ADD COLUMN` Completely Disables Data-Corruption Auditing):** Because line `598` checks `and snap_after.column_names == snap_before.column_names`, **any** migration that adds, drops, or renames a column completely skips `content_sha256` verification for that table. An `ALTER TABLE parent_table ADD COLUMN region TEXT` migration followed by `UPDATE parent_table SET description = 'WIPED'` passes with `ValidationVerdict.PASSED`!
5. **High-Severity Security & Schema Blind Spots (`S-01`, `S-02`, `S-03`, `D-03`, `C-04`):**
   - Dropping `VIEW`, `TRIGGER`, or `INDEX` objects goes 100% undetected (`D-03`).
   - Private `0o600` databases are cloned into world-readable `0o644` shadow files (`S-01`).
   - Predictable shadow filenames (`.<name>.litemigrate_shadow_<pid>`) combined with `if shadow_db.exists():` are vulnerable to a **dangling-symlink arbitrary file creation attack** (`S-02`).
   - Despite `VALIDATION_REPORT.md` Section 9 recommending `PRAGMA trusted_schema = OFF`, the code leaves `trusted_schema = 1` (`ON`) on every connection (`S-03`).

---

## 2. Master Index of Exact Source Files and Line Ranges Containing Defects

| Defect ID | Severity | Category | File Name | Exact Line Range | Summary of Defect |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **`C-01`** | **CRITICAL** | Concurrency / Data Loss | `prototype_shadow_migrate.py` | `292–305`, `358–361`, `450–452`, `617–642` | `BEGIN IMMEDIATE` is rolled back at line `302` before cloning and before `orig_digest_at_snapshot` (line `450`), causing post-clone/pre-digest writes to be silently overwritten on promotion. |
| **`C-02`** | **CRITICAL** | Concurrency / Data Loss | `prototype_shadow_migrate.py` | `617–642`, `682–693` | Unlocked TOCTOU window between CAS digest check (line `617`) and `shadow_conn.backup(source_conn)` (line `690`) silently overwrites concurrent commits. |
| **`C-03`** | **CRITICAL** | Availability / Infinite Hang | `prototype_shadow_migrate.py` | `381`, `690` | `src_conn.backup(dst_conn)` and `shadow_conn.backup(source_conn)` use `pages=-1`, which ignores `PRAGMA busy_timeout` and loops infinitely in C on `SQLITE_BUSY`. |
| **`D-01`** | **CRITICAL** | Data Integrity Blind Spot | `prototype_shadow_migrate.py` | `596–602` | `and snap_after.column_names == snap_before.column_names` disables `content_sha256` verification whenever a column is added, dropped, or renamed. |
| **`C-04`** | **HIGH** | WAL / Concurrency | `prototype_shadow_migrate.py` | `122–139`, `450`, `617` | `compute_logical_db_digest` hashes raw `.db` and `-wal` bytes without a lock; passive WAL checkpoints alter file bytes and trigger false-positive CAS aborts. |
| **`D-03`** | **HIGH** | Schema Integrity Blind Spot | `prototype_shadow_migrate.py` | `152–158`, `578–615` | `snapshot_database_tables` only queries `WHERE type = 'table'`, completely ignoring dropped `VIEW`, `TRIGGER`, and `INDEX` objects. |
| **`S-01`** | **HIGH** | Security (Info Disclosure) | `prototype_shadow_migrate.py` | `247`, `377` | Clones `0o600` source databases into `0o644` world-readable shadow files under standard `umask(0o022)`. |
| **`S-02`** | **HIGH** | Security (Symlink Race) | `prototype_shadow_migrate.py` | `244–247`, `285–290`, `377`, `413` | Predictable shadow path `.<name>.litemigrate_shadow_<pid>` + `if shadow_db.exists():` fails on dangling symlinks (`exists() == False`), creating arbitrary target files. |
| **`S-03`** | **HIGH** | Security (Untrusted Schema) | `database_setup.py`, `prototype_shadow_migrate.py` | `database_setup.py:58`, `prototype_shadow_migrate.py:376, 457, 532` | Never sets `PRAGMA trusted_schema = OFF;` on any connection despite claiming it in `VALIDATION_REPORT.md` Section 9. |
| **`P-01`** | **MEDIUM** | Reporting / Provenance | `prototype_shadow_migrate.py` | `617–653` | When `apply_to_source_on_pass=True`, `AuditReport` is constructed with pre-promotion `original_db_untouched=True` and stale `original_db_sha256_after`. |
| **`D-02`** | **MEDIUM** | Data Integrity / Float Hashing | `prototype_shadow_migrate.py` | `173–198` | `typeof(col), quote(col)` collapses IEEE 754 `-0.0` and `+0.0` into `'0.0'`, missing sign-bit mutations. |
| **`D-04`** | **MEDIUM** | SQL Lexer / Parser | `prototype_shadow_migrate.py` | `696–715` | `_split_sql_statements` splits by newline (`splitlines()`), failing with `You can only execute one statement at a time` when two statements share a line. |
| **`B-01`** | **MEDIUM** | Benchmark Methodology | `benchmark.py` | `53–60`, `162`, `178–191` | `resource.getrusage(RUSAGE_SELF).ru_maxrss` reports lifetime high-water mark of the process; running `populate_To_target_size_mb` in the same process masked per-stage memory usage as a flat `38.93 MiB`. |
| **`T-01`** | **LOW** | Test Quality / Weak Assertion | `test_shadow_migration.py` | `260–268`, `379–386` | `test_07` passed `apply_to_source_on_pass=False` (never testing concurrent writes during promotion), and `test_10` asserted `strategy_used in (APFS, FICLONE, BACKUP)` which passes even if CoW always fails. |

---

## 3. Detailed Technical Audit by Area

### Area 1 & 2: Concurrency, Snapshot Consistency & SQLite WAL Correctness

#### Defect `C-01` (Critical): Post-Clone / Pre-Digest TOCTOU Lost Update
- **Location:** `prototype_shadow_migrate.py:292–305` and `450–452`.
- **Code Inspected:**
  ```python
  # Lines 299-304 in create_shadow_database():
  try:
      sync_conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)};")
      sync_conn.execute("BEGIN IMMEDIATE;")
      sync_conn.execute("ROLLBACK;")
  finally:
      sync_conn.close()
  ```
  And in `execute_and_validate_shadow_migration()`:
  ```python
  # Lines 421-452:
  clone_result = create_shadow_database(...)
  ...
  orig_digest_at_snapshot = compute_logical_db_digest(source_path, ...)
  ```
- **Why It Fails:** `ROLLBACK;` on line `302` releases the `RESERVED` lock immediately. If an external writer commits row `777` after `create_shadow_database` copies the file (line `359` or `381`) but before line `450` computes `orig_digest_at_snapshot`, then:
  - `shadow_db` does **not** have row `777`.
  - `orig_digest_at_snapshot` (line `450`) **does** have row `777`.
  - `orig_digest_after_shadow` (line `617`) **does** have row `777`.
  - Line `618` evaluates `orig_digest_at_snapshot == orig_digest_after_shadow` as `True`, and line `640` overwrites `source_db` with `shadow_db`, destroying row `777`!
- **Empirical Evidence:** Proven in `test_adversarial_audit.py::test_finding_c01_toctou_between_barrier_rollback_and_clone_loses_committed_write` (`row_777 is None` after `ValidationVerdict.PASSED`).

#### Defect `C-02` (Critical): Post-CAS / Pre-Promotion TOCTOU Lost Update
- **Location:** `prototype_shadow_migrate.py:617–642` and `682–693`.
- **Why It Fails:** Between line `617` (`orig_digest_after_shadow = compute_logical_db_digest(source_path)`) and line `690` (`shadow_conn.backup(source_conn)`), no lock is held on `source_path`. A transaction committed in that gap is silently overwritten by `shadow_conn.backup(source_conn)`.
- **Empirical Evidence:** Proven in `test_adversarial_audit.py::test_finding_c02_toctou_between_cas_digest_check_and_promotion_loses_write` (`row_888 is None` after `ValidationVerdict.PASSED`).

#### Defect `C-03` (Critical): Infinite C-Level Hang in `sqlite3.Connection.backup()`
- **Location:** `prototype_shadow_migrate.py:381` and `690`.
- **Why It Fails:** When `shadow_conn.backup(source_conn)` is invoked while another connection holds an uncommitted `BEGIN IMMEDIATE` write lock on `source_db`, CPython's `backup_step_impl` (`pages=-1`) sleeps and retries forever in C on `SQLITE_BUSY` without consulting `PRAGMA busy_timeout`.
- **Empirical Evidence:** Proven in `test_adversarial_audit.py::test_finding_c03_sqlite_backup_api_infinite_hang_on_locked_destination` (subprocess with `busy_timeout_ms=50` remained hung after `400 ms` until terminated).

#### Defect `C-04` (High): False-Positive CAS Abort on Passive WAL Checkpoints
- **Location:** `prototype_shadow_migrate.py:122–139`.
- **Why It Fails:** `compute_logical_db_digest` hashes the raw OS file bytes of `db_path` and `db_path-wal`. Moving frames from `-wal` to `.db` via a passive checkpoint changes physical bytes without changing any logical data, causing `orig_digest_at_snapshot != orig_digest_after_shadow`.
- **Empirical Evidence:** Proven in `test_adversarial_audit.py::test_finding_c04_passive_wal_checkpoint_causes_false_positive_cas_abort`.

---

### Area 3: Promotion Atomicity & Recovery Audit

- **Is `shadow_conn.backup(source_conn)` Atomic Across Crash/Exception?**
  - We tested interrupting `s_conn.backup(d_conn, pages=1, progress=cb)` mid-copy (after 1 page out of 51) by raising a `RuntimeError` inside the progress callback and closing both connections.
  - **Verified Positive Finding:** Because `sqlite3_backup_step` writes within a write transaction on the destination database and only commits on `sqlite3_backup_finish` after the final page (`SQLITE_DONE`), interrupting `backup()` mid-copy rolled back the destination transaction cleanly, leaving `source_db` with its original 5 columns and original data intact.
- **Confirmed Defect `P-01` (Medium — Misleading Post-Promotion `AuditReport`):**
  - **Location:** `prototype_shadow_migrate.py:617–653`.
  - When `apply_to_source_on_pass=True`, `_promote_shadow_to_source` modifies `source_path` on line `640`, but lines `650–652` return `original_db_untouched=True` and the pre-promotion `orig_digest_after_shadow`! Proven in `test_finding_p01_audit_report_falsely_claims_original_db_untouched_after_promotion`.
- **Confirmed Defect `P-02` (Medium — Unhandled `OperationalError` During Promotion):**
  - `_promote_shadow_to_source` on line `640` is outside the `try ... except sqlite3.OperationalError` block (lines `420–446`), so any operational error during promotion crashes with an unhandled exception rather than returning a structured `AuditReport`.

---

### Area 4: Data Integrity & Canonical Hashing Audit

#### Defect `D-01` (Critical): Adding or Dropping a Column Completely Bypasses Content Hashing
- **Location:** `prototype_shadow_migrate.py:596–602`:
  ```python
  if (
      snap_after.row_count == snap_before.row_count
      and snap_after.column_names == snap_before.column_names
      and snap_after.content_sha256 != snap_before.content_sha256
      and tbl_name not in active_policy.allowed_mutated_tables
  ):
      unexpected_mutations.append(tbl_name)
  ```
- **Why It Is Critical:** The primary purpose of a schema migration tool is to alter schemas (e.g., `ALTER TABLE parent_table ADD COLUMN region TEXT`). Because `snap_after.column_names == snap_before.column_names` is `False` whenever a column is added, dropped, or renamed, **the prototype completely turns off content mutation detection on any table whose columns changed!**
- **Empirical Evidence:** In `test_finding_d01_adding_column_completely_disables_silent_mutation_check`, a migration ran `ALTER TABLE parent_table ADD COLUMN region TEXT` AND `UPDATE parent_table SET description = 'ALL_DESCRIPTIONS_ACCIDENTALLY_WIPED'` with an empty `MigrationPolicy()`. The prototype returned `ValidationVerdict.PASSED`!

#### Defect `D-02` (Medium): IEEE 754 `-0.0` vs `+0.0` Float Collision in `quote()`
- **Location:** `prototype_shadow_migrate.py:173–177`.
- **Why It Fails:** SQLite's `quote(-0.0)` and `quote(0.0)` both return `'0.0'`. Updating a `REAL` column from `+0.0` to `-0.0` produces an identical `content_sha256`. Proven in `test_finding_d02_quote_signed_zero_float_collision`.

#### Defect `D-03` (High): Dropped Views, Triggers, and Indexes Go 100% Undetected
- **Location:** `prototype_shadow_migrate.py:152–158`.
- **Why It Fails:** `snapshot_database_tables` filters `WHERE type = 'table'`. In `test_finding_d03_dropped_views_triggers_and_indexes_are_completely_ignored`, dropping `active_accounts_view`, `trg_prevent_negative_amount`, and `idx_child_parent_id` returned `ValidationVerdict.PASSED`!

#### Defect `D-04` (Medium): `_split_sql_statements` Fails When Two Statements Share a Line
- **Location:** `prototype_shadow_migrate.py:696–715`.
- **Why It Fails:** `_split_sql_statements` iterates over `sql_script.splitlines(keepends=True)` and checks `sqlite3.complete_statement()`. If a line contains `"ALTER TABLE parent_table ADD COLUMN a INT; ALTER TABLE parent_table ADD COLUMN b INT;"`, `complete_statement` returns `True` for the combined string, and `conn.execute(stmt)` raises `Warning: You can only execute one statement at a time`. Proven in `test_finding_d04_split_sql_statements_fails_on_multiple_statements_per_line`.

---

### Area 5 & 6: Filesystem, Platform & Security Audit

1. **Unverified macOS APFS `clonefile(2)` Assumption:**
   - `prototype_shadow_migrate.py:213–237` implements `_try_apfs_clonefile` via `ctypes`. Because the validation VM runs Linux `6.12.105+` (`x86_64`) on XFS, the Darwin code path (`sys.platform == "darwin"`) has **zero execution evidence** and remains an **Unverified Platform Assumption** until executed natively on macOS APFS.
2. **Confirmed Defect `S-01` (High — World-Readable `0o644` Shadow File):**
   - `prototype_shadow_migrate.py:247, 377`. Proven in `test_finding_s01_world_readable_shadow_file_permissions` that a `0o600` database is cloned into a `0o644` file.
3. **Confirmed Defect `S-02` (High — Predictable Filename + Dangling Symlink Clobber):**
   - `prototype_shadow_migrate.py:244, 285, 413`. Proven in `test_finding_s02_predictable_shadow_filename_dangling_symlink_clobber` that placing a dangling symlink at `.audit_target.db.litemigrate_shadow_<pid>` bypasses `shadow_db.exists()` and writes the database to the attacker's symlink target.
4. **Confirmed Defect `S-03` (High — `PRAGMA trusted_schema` Left Enabled):**
   - `database_setup.py:58`, `prototype_shadow_migrate.py:376, 457, 532`. Proven in `test_finding_s03_trusted_schema_left_enabled_on_connections` that `PRAGMA trusted_schema` is `1` (`ON`) despite `VALIDATION_REPORT.md` Section 9 claiming it should be `OFF`.

---

### Area 7: Test Quality & Benchmark Methodology Audit

1. **Why Phase 3's `test_07_concurrent_writer_lock_handling` Missed `C-01`, `C-02`, and `C-03` (`test_shadow_migration.py:231–297`):**
   - In Case 7a (line `264`), `test_07` set `apply_to_source_on_pass=False` and started the writer thread *before* `execute_and_validate_shadow_migration` was called. It never tested a writer committing *after* the clone completed (`C-01`), *after* the CAS check (`C-02`), or holding a lock *during* `_promote_shadow_to_source` (`C-03`).
2. **Why Phase 3's `test_10_backup_api_fallback_and_clone_strategy_verification` Was Weak (`test_shadow_migration.py:379–386`):**
   - Line `379` asserted `report_auto.clone_result.strategy_used in (APFS_CLONEFILE, LINUX_FICLONE, SQLITE_BACKUP_API)`. Because `SQLITE_BACKUP_API` was included in the allowed tuple, that assertion would pass even if OS copy-on-write cloning was completely broken on every platform!
3. **Why `benchmark.py` Reported an Identical `38.93 MiB` Peak RSS Across 10 MB, 100 MB, and 500 MB (`benchmark.py:53–60, 178–191`):**
   - `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` returns the **lifetime maximum RSS of the entire Python process since startup**. Because `populate_To_target_size_mb` generated a `10,000`-row batch in memory during the 10 MB setup (`~38.93 MiB` RSS), and the streaming cursor in `snapshot_database_tables` never exceeded that initial `38.93 MiB` high-water mark during the 100 MB and 500 MB runs, `get_peak_rss_mb()` simply repeated the process high-water mark (`38.93 MiB`) three times rather than measuring each scale in an isolated subprocess!

---

## 4. Summary of Deliverables & Conditions to Lift `BLOCKED` Status

All required Phase 4 audit deliverables have been generated (while preserving all original Phase 3 files unmodified):
1. `INDEPENDENT_AUDIT_REPORT.md` (this master report)
2. `CONCURRENCY_TEST_RESULTS.md` (lock-lifetime trace and `C-01`..`C-04` proofs)
3. `SECURITY_FINDINGS.md` (`S-01`..`S-04` vulnerability proofs)
4. `FIX_PLAN.md` (exact engineering remediation architecture and regression test matrix)
5. `test_adversarial_audit.py` (executable 12-test adversarial suite proving every defect in `0.769s`)

**Condition to Transition from `BLOCKED` to `GO`:** Implement the 10 targeted fixes in `FIX_PLAN.md` so that all 14 baseline tests AND all 12 adversarial tests in `test_adversarial_audit.py` pass simultaneously.
