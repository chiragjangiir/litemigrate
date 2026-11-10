# LiteMigrate Alpha Testing Program

Welcome to the **LiteMigrate Alpha Testing Program** for `v0.1.0-alpha.1`.

LiteMigrate is an open-source, local-first safety tool for SQLite database migrations. It creates an isolated, transactionally consistent shadow copy of an SQLite database, executes the migration on the shadow copy, inspects schema and data invariants, and only applies the migration to the source database if validation succeeds.

---

## 1. Safety Principles & Operating Rules

> [!CAUTION]
> **STRICT SAFETY RULE: DISPOSABLE DATA ONLY**
> **Never test LiteMigrate Alpha on production databases or databases containing private, personal, financial, or sensitive information.**
> LiteMigrate `v0.1.0-alpha.1` is an experimental pre-release. Use only disposable, test, or synthetic databases.

### Core Testing Rules
1. **Never upload database files**: LiteMigrate is local-first. We will never ask you to upload database files, credentials, or private schemas.
2. **Never attach database files to issues**: When reporting issues, share only minimal synthetic SQL reproduction scripts and sanitized log outputs.
3. **No production reliance**: LiteMigrate Alpha is not guaranteed to catch every potential migration flaw. Always maintain independent backups.

---

## 2. What LiteMigrate Does (and Does Not) Guarantee

### What LiteMigrate Guarantees:
- **Shadow Isolation**: Migrations are first executed on an isolated temporary shadow copy created via the official SQLite Online Backup API. The source database is untouched during validation.
- **Transactional Consistency**: Shadow clones capture a clean, page-level transactional snapshot of active databases (including WAL mode databases).
- **Concurrency Verification (CAS)**: Before applying validated changes to the source database, LiteMigrate verifies that the source has not changed concurrently by checking `PRAGMA data_version` and the schema cookie. If concurrent writes occurred, promotion aborts immediately without touching data.
- **Automated Rollback & Backup**: Before applying changes to the live database, an atomic pre-migration backup is created (`.bak`).
- **Destructive Mutation Protection**: By default, DROP TABLE, table truncation, and unexpected row deletion are rejected unless explicitly allowed with `--allow-destructive`.
- **Foreign Key & Integrity Checking**: Runs `PRAGMA foreign_key_check` and `PRAGMA integrity_check` on the shadow database post-migration.

### What LiteMigrate Does NOT Guarantee:
- **Zero-TOCTOU against filesystem-level modifications**: While SQLite database engine writes are detected via `PRAGMA data_version` and schema cookies, external out-of-band filesystem writes (e.g., overwriting raw `.db` bytes directly or replacing the file on disk) are outside SQLite engine tracking.
- **Arbitrary Python callable migrations**: Python callables cannot be safely audited across subprocess or CLI boundaries and are rejected. LiteMigrate strictly executes SQL-only migrations.
- **Non-SQLite databases**: LiteMigrate supports SQLite only. DuckDB, PostgreSQL, MySQL, and LibSQL are not supported.
- **Protection against malformed custom extensions**: Untrusted C extensions loaded into SQLite runtime can bypass SQLite transactional invariants.

---

## 3. How Shadow Verification Works

```
[ Active Source DB ] 
        │
        ▼ (SQLite Online Backup API)
[ Shadow DB (isolated temp copy) ]
        │
        ├─► 1. Pre-Migration Inspection (Schema, Row Fingerprints, Triggers, Pragmas)
        ├─► 2. Execute Migration SQL
        ├─► 3. Post-Migration Verification (Integrity, Foreign Keys, Schema Diffs, Row Diffs)
        ├─► 4. Destructive Policy Enforcement
        │
        ▼
   [ Verdict ] ───► FAILED: Shadow discarded, Source untouched, Audit report generated.
        │
     PASSED
        │
        ▼ (Only on `litemigrate apply --confirm`)
[ Pre-Migration Backup (.bak) ] ──► [ CAS Check (data_version) ] ──► [ Apply to Source ]
```

---

## 4. Installing the Alpha Release

The Alpha release `v0.1.0-alpha.1` can be installed in a dedicated virtual environment from GitHub Releases:

```bash
# 1. Create a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Download and install the pre-built wheel
curl -sLO https://github.com/chiragjangiir/litemigrate/releases/download/v0.1.0-alpha.1/litemigrate-0.1.0a1-py3-none-any.whl
pip install litemigrate-0.1.0a1-py3-none-any.whl

# 3. Verify installation
litemigrate --version
# Expected output: litemigrate 0.1.0a1
```

Or install from source via git:
```bash
git clone https://github.com/chiragjangiir/litemigrate.git
cd litemigrate
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 5. Quick Test Walkthrough on a Disposable Database

### Step 1: Create a Disposable SQLite Database
```bash
python3 -c '
import sqlite3
con = sqlite3.connect("disposable_test.db")
con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL, created_at TEXT)")
con.execute("INSERT INTO users VALUES (1, \"alice@example.com\", \"2026-01-01\")")
con.execute("INSERT INTO users VALUES (2, \"bob@example.com\", \"2026-01-02\")")
con.commit()
con.close()
'
```

### Step 2: Inspect Database Structure
```bash
litemigrate inspect --db disposable_test.db
```

### Step 3: Test a Safe Migration (Validation Only)
Create `add_index.sql`:
```sql
CREATE INDEX idx_users_email ON users(email);
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;
```

Validate without touching the source database:
```bash
litemigrate validate --db disposable_test.db --migration add_index.sql
```
*Observe the exit code (0), shadow execution metrics, and schema diff.*

### Step 4: Apply the Migration with Confirmation
```bash
litemigrate apply --db disposable_test.db --migration add_index.sql --confirm
```
*Observe that an automated pre-migration backup (`disposable_test.db.pre_migrate_<timestamp>.bak`) is created, CAS check passes, and migration is applied.*

### Step 5: Test a Destructive Migration
Create `drop_table.sql`:
```sql
DROP TABLE users;
```

Run validate:
```bash
litemigrate validate --db disposable_test.db --migration drop_table.sql
```
*Observe that LiteMigrate rejects this destructive change with exit code 1 (`BLOCKED_UNEXPECTED_TABLE_DROP`) because it was not declared in a migration policy.*

To explicitly permit it:
```bash
cat << 'EOF' > policy.json
{
  "allowed_dropped_tables": ["users"],
  "allowed_row_loss_tables": ["users"]
}
EOF

litemigrate validate --db disposable_test.db --migration drop_table.sql --policy policy.json
```

---

## 6. What to Test & Look For

We encourage testers to explore real-world SQLite edge cases:
- **Complex schemas**: Composite primary keys, `WITHOUT ROWID` tables, strict tables (`STRICT`), views, generated columns, triggers.
- **Foreign key cascades & constraints**: Deferred vs immediate foreign key violations.
- **Concurrency scenarios**: Concurrent read/write traffic during shadow validation (verifying CAS abort on source promotion).
- **WAL mode behavior**: Multi-connection write-ahead logging databases under active checkpointing.
- **CLI usability**: Cluttered or ambiguous outputs, unintuitive flag names, unclear diff summaries.
- **Platform compatibility**: Linux distributions, macOS (Intel & Apple Silicon), Windows (PowerShell / Command Prompt), various filesystems (ext4, XFS, ZFS, APFS, NTFS).

---

## 7. How to Submit Feedback

Please report all feedback through our structured GitHub Issue templates:

| Feedback Category | Description | Template Link |
|:---|:---|:---|
| **Bug Report** | Unexpected errors, crashes, false positives/negatives in validation | [New Bug Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_bug_report.md) |
| **Compatibility Report** | Results on unusual OS, SQLite versions, extensions, or filesystems | [New Compatibility Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_compatibility_report.md) |
| **Usability Feedback** | CLI friction, confusing diff output, suggested ergonomics | [New Usability Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_usability_feedback.md) |
| **Documentation Problem** | Inaccurate CLI instructions, broken examples, unclear wording | [New Docs Report](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_documentation_problem.md) |

For detailed guidance on preparing sanitized reproduction cases, see [docs/ALPHA_FEEDBACK_GUIDE.md](docs/ALPHA_FEEDBACK_GUIDE.md).

