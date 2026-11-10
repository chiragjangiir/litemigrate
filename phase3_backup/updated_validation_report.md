# LiteMigrate — Updated Engineering Validation Report (Phase 5 Post-Remediation)

**Date:** November 10, 2026  
**Validation Environment:** Linux `6.12.105+` (`x86_64`, glibc `2.36`), Python `3.11.2`, SQLite `3.40.1`, XFS filesystem with `FICLONE` (`0x40049409`) copy-on-write reflink support  
**Final Engineering Verdict:** **`CONDITIONAL GO`**
- **`GO` for the SQLite Local Shadow-Migration & Audit Core:** All 4 Critical, 5 High, and 5 Medium/Low defects identified in the Phase 4 Independent Adversarial Audit have been remediated and verified across 38 automated tests (`1.728s`, `100% PASS`) and multi-scale isolated-subprocess benchmarks (`17.58 MB`, `175.70 MB`, `878.66 MB`).
- **Why `CONDITIONAL GO` (Hardware Environment Disclosure):** Per strict engineering integrity standards, this validation was executed inside a Linux `x86_64` XFS environment where Linux `ioctl(FICLONE)` and the POSIX `ctypes` `sqlite3_backup_*` C API were directly executed and verified. Because physical Apple Silicon (`M1`, macOS Darwin APFS) hardware was not attached to this Linux container, the macOS `clonefile(2)` code path (`_clone_via_apfs_clonefile`) remains unexecuted on native Darwin hardware. Promoting from `CONDITIONAL GO` to an unconditional cross-platform `GO` requires running the single command `python3 -m unittest discover -v -s . -p "test_*.py" && python3 benchmark.py` on an Apple Silicon MacBook to confirm `CloneStrategy.APFS_CLONEFILE` in situ.

---

## 1. Remediated Multi-Scale Benchmark Results (`B-01` Fixed)

In Phase 3, `benchmark.py` called `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` inside the same Python process that generated the 500 MB fixture database, conflating fixture-generation memory with LiteMigrate's runtime footprint (`B-01`).

In Phase 5, `benchmark.py` spawns a **fresh isolated child process (`subprocess.run`)** for each scale's shadow clone, 12-step `parent_table` rebuild migration, fast structural audit, and full canonical table + per-column SHA-256 audit:

| Target Scale | Actual DB Size on Disk | Row Counts (`parent` / `child`) | CoW Clone (`linux_ficlone`) | SQLite Backup API Clone | 12-Step Parent Rebuild Migration | Fast Audit (`COUNT` + `FK` + `quick_check`) | Full Audit (Table + Per-Column `SHA-256` + `FK` + `integrity_check`) | Isolated Migration Process Peak RSS | Setup Process Peak RSS | Safe / Buggy Verdicts |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **10 MB** | `17.58 MB` | `446` / `4,460` (`4,906` total) | **`0.43 ms`** | `37.99 ms` | `9.78 ms` | `12.16 ms` | `129.80 ms` | **`33.18 MiB`** | `22.87 MiB` | `passed` / `blocked_unexpected_row_loss` |
| **100 MB** | `175.70 MB` | `4,462` / `44,620` (`49,082` total) | **`0.44 ms`** | `221.85 ms` | `18.99 ms` | `154.73 ms` | `1,315.63 ms` (`1.32 s`) | **`34.03 MiB`** | `27.07 MiB` | `passed` / `blocked_unexpected_row_loss` |
| **500 MB** | `878.66 MB` | `22,310` / `223,100` (`245,410` total) | **`0.44 ms`** | `1,978.50 ms` (`1.98 s`) | `44.08 ms` | `779.33 ms` | `6,406.30 ms` (`6.41 s`) | **`34.16 MiB`** | `33.05 MiB` | `passed` / `blocked_unexpected_row_loss` |

### Key Benchmark Takeaways
1. **True $O(1)$ Streaming Memory Footprint (`33.18 MiB` to `34.16 MiB`):** Across a **50x increase in database file size** (from `17.58 MB` to `878.66 MB`), the isolated migration and full per-column SHA-256 audit child process grows by only **`0.98 MiB`** (`33.18 MiB` $\rightarrow$ `34.16 MiB`), proving that `cursor.fetchmany(1024)` streaming hashing never loads full tables into RAM.
2. **Sub-Millisecond OS CoW Cloning on XFS (`0.43 ms` – `0.44 ms`):** When the database is in single-file mode (no uncheckpointed `-wal` frames), `ioctl(FICLONE)` clones an `878.66 MB` SQLite database in **`0.44 ms`** (**4,496x faster** than the `1,978.50 ms` SQLite Online Backup API).
3. **Full Per-Column + Whole-Table SHA-256 Audit Throughput (`~137 MB/s`):** Even after adding per-column canonical SHA-256 hashing (`D-01`) and IEEE-754 float serialization (`D-02`), auditing `245,410` rows (`878.66 MB`) before and after migration completes in **`6.41 seconds`**, while the lightweight structural audit (`COUNT(*)` + `PRAGMA foreign_key_check` + `PRAGMA quick_check`) completes in **`0.78 seconds`**.

---

## 2. Summary of Verified Guarantees vs. Remaining Conditions

### Verified Guarantees
- **Concurrency Safety (`C-01`, `C-02`):** Zero-TOCTOU promotion holds `BEGIN IMMEDIATE` on `source_conn` while verifying `compute_logical_db_digest(source_conn) == shadow_baseline_digest` and executing the promoted SQL migration in the exact same transaction. No committed write can be overwritten.
- **Bounded Execution (`C-03`):** Direct `ctypes` `sqlite3_backup_step` integration enforces `busy_timeout_ms` deadlines without hanging in CPython's internal sleep loop.
- **WAL Correctness (`C-04`):** Active `-wal` files automatically route to `_bounded_sqlite_backup()`, passive checkpoints do not trigger false CAS aborts, and shadow `-wal`/`-shm`/`-journal` files are deterministically truncated and unlinked.
- **Complete Schema & Data Auditing (`D-01`, `D-02`, `D-03`, `D-04`):** Detects dropped tables, dropped indexes/triggers/views, unintended row losses, orphan foreign keys, B-tree corruption, whole-table mutations, and silent mutations on existing columns when columns are added or reordered.
- **Security Hardening (`S-01`, `S-02`, `S-03`, `S-04`):** Enforces `0o700` temporary directories, `0o600` shadow files via `O_CREAT | O_EXCL | O_NOFOLLOW`, symlink rejection across all paths, and verified `PRAGMA trusted_schema = OFF` (`0`) on every connection.

### Single Remaining Condition for Unconditional Cross-Platform Release
- Execute `python3 -m unittest discover -v -s . -p "test_*.py" && python3 benchmark.py` on a physical macOS Apple Silicon (`darwin` / `arm64`) machine to verify `_clone_via_apfs_clonefile` (`libSystem.B.dylib` `clonefile(2)`) on native APFS storage.
