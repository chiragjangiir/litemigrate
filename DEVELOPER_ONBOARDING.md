# LiteMigrate — Developer Onboarding Guide

Welcome to **LiteMigrate**! This guide takes you from zero to executing your first shadow-verified SQLite migration in under 5 minutes.

---

## The 9-Step Onboarding Journey

```
1. Discover ──► 2. Understand ──► 3. Install ──► 4. Create Disposable DB ──► 5. Inspect
                                                                                  │
  9. Report ◄── 8. Apply ◄── 7. Read Report ◄── 6. Validate ◄─────────────────────┘
```

---

## Step 1: Discover

LiteMigrate is an open-source, local-first safety utility for SQLite database migrations.

- **GitHub Repository**: [https://github.com/chiragjangiir/litemigrate](https://github.com/chiragjangiir/litemigrate)
- **Current Release**: `v0.1.0-alpha.1` (Experimental Alpha)
- **License**: Apache-2.0

---

## Step 2: Understand the Purpose

In SQLite, running a migration directly against your live database is dangerous:
- Foreign key cascade deletions can silently wipe child tables.
- Flawed table rebuilds (12-step rebuilds) can drop columns or truncate data without throwing syntax errors.
- Concurrent writes can cause lock contention or lost updates.

**LiteMigrate solves this by creating an isolated, copy-on-write shadow copy of your database in less than a millisecond, executing the migration on the shadow copy, checking all relational and data invariants, and only promoting the migration to the live database if all checks pass.**

---

## Step 3: Install the Alpha Release

> [!NOTE]
> LiteMigrate requires **Python 3.9+** and standard `sqlite3`. During the Alpha phase, artifacts are distributed directly via GitHub Releases (not yet on PyPI).

```bash
# 1. Create a dedicated directory and virtual environment
mkdir litemigrate-sandbox && cd litemigrate-sandbox
python3 -m venv .venv
source .venv/bin/activate

# 2. Download and install the pre-built Alpha wheel
curl -sLO https://github.com/chiragjangiir/litemigrate/releases/download/v0.1.0-alpha.1/litemigrate-0.1.0a1-py3-none-any.whl
pip install litemigrate-0.1.0a1-py3-none-any.whl

# 3. Verify installation
litemigrate --version
# Expected output: litemigrate 0.1.0a1
```

---

## Step 4: Create a Disposable SQLite Database

Never test with real production data. Run this script to generate a synthetic database:

```bash
python3 -c '
import sqlite3

con = sqlite3.connect("app_dev.db")
con.execute("PRAGMA foreign_keys = ON;")
con.execute("""
    CREATE TABLE teams (
        team_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        plan TEXT DEFAULT "starter"
    );
""")
con.execute("""
    CREATE TABLE members (
        member_id INTEGER PRIMARY KEY,
        team_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    );
""")

con.executemany("INSERT INTO teams VALUES (?, ?, ?)", [
    (1, "Core Platform", "enterprise"),
    (2, "Data Engineering", "team"),
])

con.executemany("INSERT INTO members VALUES (?, ?, ?, ?)", [
    (101, 1, "Alice", "alice@example.com"),
    (102, 1, "Bob", "bob@example.com"),
    (201, 2, "Charlie", "charlie@example.com"),
])

con.commit()
con.close()
print("Created disposable database: app_dev.db")
'
```

---

## Step 5: Run Inspect

Inspect the schema structure, journal mode, foreign key status, and database integrity without exposing sensitive rows:

```bash
litemigrate inspect --db app_dev.db
```

Output highlights:
```text
═════════════════════════════════════════════════════════════════
 LiteMigrate — Database Inspection Report
═════════════════════════════════════════════════════════════════
  Database Path:         .../app_dev.db
  SQLite Version:        3.43.2
  Journal Mode:          DELETE
  Foreign Keys Enabled:  Yes
  Database Integrity:    PASSED

  User Tables:
    • members
    • teams
═════════════════════════════════════════════════════════════════
```

---

## Step 6: Run Validate (Safe Migration)

Create a migration script adding an index and a new column:

```bash
cat << 'EOF' > 001_add_seats.sql
ALTER TABLE teams ADD COLUMN max_seats INTEGER DEFAULT 10;
CREATE INDEX idx_members_team ON members(team_id);
EOF
```

Run validation. **This operates strictly on an isolated shadow copy; `app_dev.db` remains 100% untouched:**

```bash
litemigrate validate --db app_dev.db --migration 001_add_seats.sql --output report.json
```

---

## Step 7: Understand the Report

LiteMigrate displays a clear verdict banner:
- **`Verdict: PASSED`**: All integrity checks, foreign key checks, and row preservation invariants succeeded.
- **`Source DB Untouched: Yes`**: Confirms no write occurred against `app_dev.db`.
- **`Clone Strategy Used`**: Reports whether macOS APFS reflink, Linux FICLONE, or SQLite Backup API was utilized.
- **`Clone Duration`**: Shows how fast the isolated shadow copy was created (typically < 1 ms).

You can inspect the full JSON report at any time:
```bash
litemigrate report --input report.json
```

---

## Step 8: Safely Test Apply

Now promote the validated migration to the source database:

```bash
litemigrate apply --db app_dev.db --migration 001_add_seats.sql --confirm
```

What happened:
1. Re-validated on a fresh shadow clone.
2. Created an atomic pre-promotion backup file (`app_dev.db.pre_migrate_<timestamp>.bak`).
3. Acquired an exclusive writer lock (`BEGIN IMMEDIATE`).
4. Verified that no concurrent writer altered `app_dev.db` while validation occurred (CAS check).
5. Applied migration and committed atomically.

Verify the new schema:
```bash
sqlite3 app_dev.db ".schema teams"
# Output shows max_seats column is now present!
```

---

## Step 9: Report a Problem or Anomaly

If you encounter unexpected behavior, foreign key false-positives, or platform anomalies:
1. Review [docs/ALPHA_FEEDBACK_GUIDE.md](docs/ALPHA_FEEDBACK_GUIDE.md).
2. Gather system information using:
   ```bash
   python3 -c "import platform, sqlite3; print(platform.platform(), sqlite3.sqlite_version)"
   ```
3. Open a structured issue using our GitHub templates:
   - [Bug Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_bug_report.md)
   - [Compatibility Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_compatibility_report.md)
   - [Usability Feedback](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_usability_feedback.md)
   - [Documentation Problem](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_documentation_problem.md)

> [!CAUTION]
> Remember: **Never attach database files or private data.** Use only disposable synthetic reproductions.

