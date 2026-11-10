# r/Python Launch Package: LiteMigrate

This document contains a tailored draft post for **r/Python**, adhering to the subreddit's project showcase rules, self-promotion guidelines, and community expectations.

> [!IMPORTANT]
> **DO NOT POST EXTERNALLY WITHOUT EXPLICIT APPROVAL.**
> This post is prepared for review only.

---

## Subreddit Context & Guidelines Check (r/Python)

- **Post Type**: Project Showcase / Discussion.
- **Rule Compliance**:
  - Must be open-source and written in Python (LiteMigrate is 100% Python with standard library `sqlite3` and `ctypes`).
  - Must provide a direct GitHub link to source code.
  - Must explain **what the project does**, **target audience**, and **how it differs from existing tools** (e.g. Alembic, raw sqlite3).
  - Must avoid sensationalized titles or affiliate links.
- **Recommended Flair**: `Project` or `Showcase`.

---

## Suggested Post Title

`[Project] LiteMigrate: Pre-validate SQLite migrations on an isolated shadow copy before promotion`

*(Alternative: `LiteMigrate: A local-first Python tool to test SQLite migrations in a copy-on-write sandbox before touching your database`)*

---

## Post Body Draft

```markdown
### What My Project Does

**LiteMigrate** is a local-first Python CLI tool and library that lets developers test SQLite database migrations against an isolated, copy-on-write "shadow" clone of their database before promoting changes to production.

In SQLite, running migrations directly against a live file is risky. Unlike Postgres or MySQL, SQLite has limited `ALTER TABLE` capabilities and often requires the 12-step table rebuild procedure (creating a temporary table, copying rows via `INSERT INTO ... SELECT`, dropping the original table, and renaming). A single omitted column or an unintended `ON DELETE CASCADE` action will execute with exit code 0 while silently truncating data or wiping related tables.

LiteMigrate solves this by enforcing a **shadow verification workflow**:
1. **Sub-millisecond cloning**: Uses OS-level copy-on-write reflinks (APFS `clonefile` on macOS, `ioctl(FICLONE)` on Linux) or the SQLite Online Backup API to clone an active database in under 1 ms without duplicating disk blocks.
2. **Multi-invariant audit**: Executes the migration SQL strictly inside the shadow copy, verifying `PRAGMA foreign_key_check`, `PRAGMA integrity_check`, schema diffs, and streaming row fingerprints (with IEEE-754 signed zero float discrimination and rowid aliasing safety).
3. **Safe promotion**: When running `litemigrate apply --confirm`, it acquires an exclusive writer lock (`BEGIN IMMEDIATE`), verifies `PRAGMA data_version` hasn't changed concurrently (Compare-And-Swap), creates a pre-promotion backup file (`.bak`), and commits changes.

---

### Target Audience

- **Python developers** using SQLite in local-first apps (FastAPI, Flask, Django, Litestar), desktop applications (Tauri, Electron), or CLI tools.
- **Data engineers and DevOps teams** wanting automated migration validation in CI/CD before running production rollouts.
- **SQLite enthusiasts** who want programmatic foreign-key and integrity guarantees before modifying live databases.

---

### Comparison with Existing Tools (Alembic / Django Migrations)

LiteMigrate is **not** an ORM or a migration generator. It is an **execution and safety harness**:
- Migration frameworks (Alembic, Django migrations, Flyway) answer: *"Did the SQL statements execute without throwing an error?"*
- LiteMigrate answers: *"Did existing rows survive? Did foreign key relationships hold? Is physical page integrity intact? Did concurrent writers commit data while validation was running?"*

You can use LiteMigrate alongside Alembic or plain SQL migration files.

---

### 2-Minute Disposable Walkthrough

```bash
# 1. Install the Alpha wheel from GitHub Releases
curl -sLO https://github.com/chiragjangiir/litemigrate/releases/download/v0.1.0-alpha.1/litemigrate-0.1.0a1-py3-none-any.whl
pip install litemigrate-0.1.0a1-py3-none-any.whl

# 2. Create a disposable test database
python3 -c "
import sqlite3
con = sqlite3.connect('test.db')
con.execute('CREATE TABLE users (id INT PRIMARY KEY, email TEXT, name TEXT)')
con.execute('INSERT INTO users VALUES (1, \"alice@example.com\", \"Alice\")')
con.commit()
"

# 3. Inspect schema structure
litemigrate inspect --db test.db

# 4. Validate migration on shadow copy (test.db remains completely untouched!)
echo "ALTER TABLE users ADD COLUMN age INT DEFAULT 25;" > add_age.sql
litemigrate validate --db test.db --migration add_age.sql

# 5. Apply safely with pre-promotion backup & CAS check
litemigrate apply --db test.db --migration add_age.sql --confirm
```

---

### Current Status & Feedback Request

LiteMigrate is currently an **experimental Alpha (`v0.1.0-alpha.1`)**.
- It is 100% local-first: zero telemetry, zero cloud services, zero external network calls.
- It is tested against Python 3.9, 3.10, 3.11, and 3.12 across macOS and Ubuntu Linux (80 automated tests passing in CI).
- We have not published to PyPI yet (installing via the GitHub Release wheel is the supported path for Alpha testers).

**Please test exclusively on disposable synthetic databases.**

- **Source Code**: https://github.com/chiragjangiir/litemigrate
- **Alpha Release**: https://github.com/chiragjangiir/litemigrate/releases/tag/v0.1.0-alpha.1
- **Tester Quickstart**: https://github.com/chiragjangiir/litemigrate/blob/main/docs/TESTER_QUICKSTART.md

I'd love feedback from the Python community on CLI ergonomics, failure modes, and compatibility across Linux filesystems!
```
