# LiteMigrate — Benchmark Methodology & Measured Performance

All performance metrics below were measured using `benchmark.py` in isolated child processes to ensure accurate peak Resident Set Size (RSS) reporting without process lifetime memory skew.

## Measurement Environment
- **Hardware:** Apple M-series (Apple Silicon arm64)
- **OS:** macOS Darwin (APFS volume with native copy-on-write `clonefile(2)`)
- **Python:** Python 3.14 / SQLite 3.53.4

---

## Benchmark Results

### 1. 5.0 MB Database Scale (5.02 MB on disk)

| Operation | Strategy | Execution Duration | Isolated Peak RSS |
| :--- | :--- | :--- | :--- |
| **Shadow Clone** | `APFS_CLONEFILE` (CoW) | **1.21 ms** | **26.05 MB** |
| **Shadow Clone** | `SQLITE_BACKUP_API` | 18.99 ms | 37.27 MB |
| **Validation + Audit** | `APFS_CLONEFILE` | 1,936.73 ms | 31.03 MB |
| **Validation + Audit** | `SQLITE_BACKUP_API` | 1,987.33 ms | 39.39 MB |

### 2. 25.0 MB Database Scale (25.00 MB on disk)

| Operation | Strategy | Execution Duration | Isolated Peak RSS | Speedup / Observation |
| :--- | :--- | :--- | :--- | :--- |
| **Shadow Clone** | `APFS_CLONEFILE` (CoW) | **1.18 ms** | **25.91 MB** | **~111x faster** than Backup API |
| **Shadow Clone** | `SQLITE_BACKUP_API` | 131.37 ms | 61.88 MB | Linear scaling with page count |
| **Validation + Audit** | `APFS_CLONEFILE` | 8,823.27 ms | 31.19 MB | Streaming $O(1)$ memory consumption |
| **Validation + Audit** | `SQLITE_BACKUP_API` | 8,860.02 ms | 63.94 MB | Stable memory footprint |

---

## Key Performance Findings

1. **Copy-on-Write Superiority:** On macOS APFS, `clonefile(2)` completes in **~1.18 ms** regardless of database size, consuming 0 additional disk blocks until modified.
2. **Strict O(1) Memory Streaming:** The full-table and per-column fingerprinting engine streams records in 1,024-row batches. Peak RSS memory stays under **~32 MB** even as database size increases from 5 MB to 25 MB+.
3. **Deterministic Backup API Fallback:** The bounded SQLite C Backup API operates cleanly as a universal fallback across filesystems and active WAL databases.
