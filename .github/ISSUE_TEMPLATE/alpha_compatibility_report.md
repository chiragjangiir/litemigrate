---
name: Alpha Compatibility Report
about: Report compatibility results across platforms, filesystems, SQLite versions, or extensions
title: '[Alpha Compatibility]: '
labels: ['alpha', 'compatibility']
assignees: ''
---

> **CRITICAL PRIVACY WARNING**
> **DO NOT ATTACH DATABASE FILES, PASSWORDS, CONFIDENTIAL INFORMATION, OR REAL PRODUCTION DATA.**
> All reports must use disposable test data or synthetic minimal reproduction scripts.

### 1. Disposable Data Confirmation
- [ ] I confirm that I am using a **disposable, non-production SQLite database** and no proprietary or sensitive data is included in this report.

### 2. Environment Details
- **LiteMigrate Version**: 0.1.0-alpha.1 (`litemigrate --version`)
- **Operating System & Kernel**: [e.g., FreeBSD 14.0, Alpine Linux 3.19 (musl), Windows Server 2022]
- **Filesystem & Mount Type**: [e.g., ZFS, btrfs, NFS, CIFS, tmpfs, APFS, NTFS]
- **Python Version & Implementation**: [e.g., CPython 3.12.1, PyPy 3.10]
- **SQLite Library Version**: [e.g., 3.39.5, 3.45.1] (`python3 -c "import sqlite3; print(sqlite3.sqlite_version)"`)
- **SQLite Compile Options / Extensions**: [e.g., FTS5, JSON1, SpatiaLite, R*Tree - check with `python3 -c "import sqlite3; c = sqlite3.connect(':memory:'); print([r[0] for r in c.execute('PRAGMA compile_options')])"`]

### 3. Verification Scenario Tested
- [ ] Standard SQLite database clone & backup (`sqlite3_backup_*`)
- [ ] WAL mode active database
- [ ] Large table / multi-index migration
- [ ] WITHOUT ROWID tables
- [ ] Strict tables (`STRICT` mode)
- [ ] Views, Triggers, or Virtual Tables (FTS5, etc.)
- [ ] Non-ASCII column / table names

### 4. Exact Command Executed
```bash
litemigrate validate test.db --migration-file migration.sql
```

### 5. Observed Compatibility Status
- **Result**: [PASS / FAIL / PARTIAL / UNEXPECTED WARNING]
- **Description**: What worked as expected and what failed or exhibited anomalies.

### 6. Sanitized Output / Logs
```text
<!-- Paste sanitized log or terminal output here -->
```
