# LiteMigrate Alpha Feedback & Reporting Guide

Thank you for participating in the **LiteMigrate Alpha testing program**!

Your feedback helps us harden LiteMigrate's safety guarantees, improve ergonomics, and catch edge cases across platforms and filesystems.

---

## 1. Strict Privacy & Security Rules

> [!CAUTION]
> **NEVER SEND REAL OR PRIVATE DATA**
> - **DO NOT upload database files (`.db`, `.sqlite`, `.db-wal`) to GitHub issues.**
> - **DO NOT include passwords, connection strings, auth tokens, or PII.**
> - **DO NOT share proprietary business data or schema names.**
> All reports must use synthetic minimal reproductions or sanitized outputs.

---

## 2. Feedback Categories & Direct Links

Select the appropriate template when opening an issue:

1. **[Bug Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_bug_report.md)**
   - Crashes, uncaught exceptions, unexpected validation verdicts, or incorrect schema/row diffs.
2. **[Compatibility Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_compatibility_report.md)**
   - Testing on specific operating systems, unusual filesystems (ZFS, NFS, CIFS), SQLite compile flags, or SQLite extensions.
3. **[Usability Feedback](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_usability_feedback.md)**
   - CLI design, confusing error messages, diff visual clarity, flag ergonomics, or unexpected terminal formatting.
4. **[Documentation Problem](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_documentation_problem.md)**
   - Inaccurate commands, broken links, unclear explanations, or misleading safety wording.

---

## 3. How to Create a Minimal Reproduction

A good reproduction consists of two short SQL snippets:
1. **Initial Schema & Synthetic Data** (Setup SQL)
2. **Migration SQL** that triggers the behavior

### Example Minimal Reproduction:
```sql
-- 1. Setup SQL (synthetic minimal case)
CREATE TABLE inventory (
    item_id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL,
    qty INTEGER DEFAULT 0
);
INSERT INTO inventory (item_id, sku, qty) VALUES (1, 'WIDGET-A', 10);

-- 2. Migration SQL
ALTER TABLE inventory ADD COLUMN min_order INTEGER NOT NULL; -- Note: missing DEFAULT
```

---

## 4. Extracting Sanitized Terminal Outputs

When providing terminal output:
1. Replace private user home directory paths (e.g. `/Users/johndoe/projects/...` -> `/path/to/project/...`).
2. Include the exact command that was run.
3. Copy the full error message and stack trace if one was printed.

```bash
# Example clean reproduction trace:
$ litemigrate validate app.db --migration-file migration.sql
[FAIL] Migration rejected:
Error: Cannot add a NOT NULL column with no default value
Exit Code: 2
```

---

## 5. System Diagnostic Helper

To quickly gather your exact environment details for your report, run this one-line diagnostic command:

```bash
python3 -c '
import platform, sqlite3, sys
print(f"OS: {platform.system()} {platform.release()} ({platform.machine()})")
print(f"Python: {sys.version.split()[0]}")
print(f"SQLite Library: {sqlite3.sqlite_version}")
print(f"SQLite Source ID: {sqlite3.sqlite_version}")
'
```

Paste the output into the **Environment Details** section of your issue template.

