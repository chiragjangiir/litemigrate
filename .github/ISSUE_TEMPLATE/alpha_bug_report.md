---
name: Alpha Bug Report
about: Report a bug, crash, or unexpected validation verdict in LiteMigrate Alpha
title: '[Alpha Bug]: '
labels: ['alpha', 'bug']
assignees: ''
---

> **CRITICAL PRIVACY WARNING**
> **DO NOT ATTACH DATABASE FILES, PASSWORDS, CONFIDENTIAL INFORMATION, OR REAL PRODUCTION DATA.**
> All reports must use disposable test data or synthetic minimal reproduction scripts.

### 1. Disposable Data Confirmation
- [ ] I confirm that I am using a **disposable, non-production SQLite database** and no proprietary or sensitive data is included in this report.

### 2. Environment Details
- **LiteMigrate Version**: 0.1.0-alpha.1 (check with `litemigrate --version`)
- **Operating System & Architecture**: [e.g., macOS 14.5 arm64, Ubuntu 22.04 x86_64, Windows 11 x86_64]
- **Filesystem**: [e.g., APFS, ext4, NTFS, tmpfs]
- **Python Version**: [e.g., 3.11.4] (`python3 --version`)
- **SQLite Library Version**: [e.g., 3.42.0] (`python3 -c "import sqlite3; print(sqlite3.sqlite_version)"`)

### 3. Exact Command Executed
```bash
# Paste the exact command line executed, e.g.:
litemigrate validate app.db --migration-file migration.sql
```

### 4. Minimal Reproduction Scenario
**Baseline Schema / Setup SQL:**
```sql
-- Minimal DDL to recreate the baseline table
```

**Migration SQL:**
```sql
-- Migration script executed
```

### 5. Expected Behavior
A concise description of what you expected LiteMigrate to do.

### 6. Actual Behavior & Verdict
A concise description of what happened instead.

### 7. Sanitized CLI Output / Traceback
```text
<!-- Paste terminal output or error traceback here. Redact any local username paths if desired. -->
```

