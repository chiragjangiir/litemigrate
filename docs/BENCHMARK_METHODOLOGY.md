# LiteMigrate Benchmark Methodology & Performance Targets

This document outlines the reproducible testing framework used to measure shadow migration latency, memory consumption, and I/O overhead across various operating systems and storage engines.

---

## 1. Benchmarking Objectives

LiteMigrate is engineered to introduce minimal overhead when validating SQLite database changes before production promotion. Our benchmark framework profiles:
1. **Clone Latency**: Measuring clone duration across APFS copy-on-write (`clonefile`), raw file copy (`shutil.copy2`), and SQLite online backup API (`conn.backup`).
2. **Fingerprint Overhead**: Measuring SHA256 streaming hash throughput on tables with 10k, 100k, and 1,000,000 rows.
3. **Peak Memory Usage**: Ensuring peak resident set size (RSS) remains under **64 MB** regardless of database size via batched streaming cursors.

---

## 2. Workload Test Matrices

| Workload Tier | Database Size | Row Count | Index Count | Strategy Target | Max Target Latency |
|:--------------|:--------------|:----------|:------------|:----------------|:-------------------|
| **Tier S** (Micro)   | 5 MB          | 10,000    | 3           | APFS / Copy     | < 25 ms            |
| **Tier M** (Standard)| 50 MB         | 100,000   | 5           | APFS / Copy     | < 180 ms           |
| **Tier L** (Large)   | 500 MB        | 1,000,000 | 8           | APFS Clonefile  | < 950 ms           |

---

## 3. Running Local Benchmarks

To execute the standardized benchmark suite:

```bash
# Generate synthetic dataset and profile shadow migration
PYTHONPATH=src python3 benchmark.py --rows 100000 --output docs/benchmark-results.json
```

### Reproducibility Environment
- **CPU**: Apple M-series / AMD Ryzen 9 / Intel Xeon
- **Storage**: PCIe Gen4 NVMe or Apple APFS SSD
- **Python**: 3.9+ with standard library `sqlite3`
