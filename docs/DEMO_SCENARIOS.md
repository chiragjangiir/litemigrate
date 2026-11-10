# LiteMigrate — Empirical Demonstration Scenarios

This document provides six fully reproducible, disposable demonstration scenarios for **LiteMigrate `v0.1.0-alpha.1`**.

Every command and terminal output in this document was empirically executed and captured in a clean test environment.

---

## Scenario 1: Successful Additive Migration

### Objective
Demonstrate that a standard, non-destructive migration (adding a column and an index) validates cleanly on an isolated shadow copy, reports `Verdict: PASSED`, leaves the source database untouched during validation, and applies safely when confirmed.

### 1. Setup Instructions
```bash
mkdir -p /tmp/litemigrate_demo_s1 && cd /tmp/litemigrate_demo_s1

python3 -c '
import sqlite3
con = sqlite3.connect("demo1.db")
con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT)")
con.executemany("INSERT INTO users VALUES (?, ?, ?)", [
    (1, "alice@example.com", "Alice"),
    (2, "bob@example.com", "Bob"),
])
con.commit()
con.close()
'
```

### 2. Migration SQL (`add_column.sql`)
```sql
ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT '2026-01-01';
CREATE INDEX idx_users_created ON users(created_at);
```

### 3. Exact CLI Commands
```bash
# A. Inspect
litemigrate inspect --db demo1.db

# B. Validate on Shadow
litemigrate validate --db demo1.db --migration add_column.sql

# C. Apply to Source
litemigrate apply --db demo1.db --migration add_column.sql --confirm
```

### 4. Actual CLI Output
```text
═════════════════════════════════════════════════════════════════
 LiteMigrate — Database Inspection Report
═════════════════════════════════════════════════════════════════
  Database Path:         /tmp/litemigrate_demo_s1/demo1.db
  SQLite Version:        3.43.2
  Journal Mode:          DELETE
  File Size:             12,288 bytes
  Table Count:           1
  Schema Objects:        0
  Foreign Keys Enabled:  Yes
  Database Integrity:    PASSED

  User Tables:
    • users
═════════════════════════════════════════════════════════════════
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — VALIDATE
═════════════════════════════════════════════════════════════════
  Verdict:               PASSED
  Source Database:       /tmp/litemigrate_demo_s1/demo1.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.33 ms
  Migration Execution:   0.48 ms
  Audit Duration:        0.23 ms
  Total Elapsed Time:    2.91 ms

  Audit Findings & Details:
    • Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.
═════════════════════════════════════════════════════════════════
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — APPLY
═════════════════════════════════════════════════════════════════
  Verdict:               PASSED
  Source Database:       /tmp/litemigrate_demo_s1/demo1.db
  Promoted to Source:    Yes
  Source DB Untouched:   No
  Pre-Promote Backup:    /tmp/litemigrate_demo_s1/demo1.db.pre_migrate_1794311745546071000.bak
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.33 ms
  Migration Execution:   0.49 ms
  Audit Duration:        0.24 ms
  Total Elapsed Time:    7.10 ms

  Audit Findings & Details:
    • Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.
    • Successfully promoted migration to source database (backup at /tmp/litemigrate_demo_s1/demo1.db.pre_migrate_1794311745546071000.bak).
═════════════════════════════════════════════════════════════════
```

### 5. Explanation
- The shadow copy was created in 0.33 ms via copy-on-write reflink.
- During `validate`, `demo1.db` was untouched (`Source DB Untouched: Yes`).
- During `apply`, LiteMigrate created an atomic pre-promotion backup (`.bak`), verified that no concurrent writes modified `demo1.db`, and applied the migration. Exit code: `0`.

---

## Scenario 2: Destructive Migration Blocked by Policy

### Objective
Demonstrate that an accidental or unauthorized `DROP TABLE` is intercepted and blocked by default, protecting live data, but can be permitted if declared in an explicit `policy.json`.

### 1. Setup Instructions
```bash
mkdir -p /tmp/litemigrate_demo_s2 && cd /tmp/litemigrate_demo_s2

python3 -c '
import sqlite3
con = sqlite3.connect("demo2.db")
con.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, total REAL)")
con.executemany("INSERT INTO orders VALUES (?, ?)", [(1, 99.0), (2, 149.5)])
con.commit()
con.close()
'
```

### 2. Migration SQL (`drop_table.sql`)
```sql
DROP TABLE orders;
```

### 3. Exact CLI Commands
```bash
# Step A: Validate without policy (should be BLOCKED)
litemigrate validate --db demo2.db --migration drop_table.sql

# Step B: Declare explicit policy allowing the drop
cat << 'EOF' > allow_drop_policy.json
{
  "allowed_dropped_tables": ["orders"],
  "allowed_row_loss_tables": ["orders"]
}
EOF

# Step C: Validate with explicit policy (should PASS)
litemigrate validate --db demo2.db --migration drop_table.sql --policy allow_drop_policy.json
```

### 4. Actual CLI Output
**Step A (Default Strict Policy):**
```text
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — VALIDATE
═════════════════════════════════════════════════════════════════
  Verdict:               BLOCKED_UNEXPECTED_TABLE_DROP
  Source Database:       /tmp/litemigrate_demo_s2/demo2.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.33 ms
  Migration Execution:   0.45 ms
  Audit Duration:        0.07 ms
  Total Elapsed Time:    2.28 ms

  Audit Findings & Details:
    • Unexpected dropped table 'orders' was not declared in policy.allowed_dropped_tables.

  Dropped Tables:        orders
═════════════════════════════════════════════════════════════════
Exit code: 1
```

**Step C (With Explicit Policy):**
```text
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — VALIDATE
═════════════════════════════════════════════════════════════════
  Verdict:               PASSED
  Source Database:       /tmp/litemigrate_demo_s2/demo2.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.36 ms
  Migration Execution:   0.40 ms
  Audit Duration:        0.08 ms
  Total Elapsed Time:    2.63 ms

  Audit Findings & Details:
    • Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.

  Dropped Tables:        orders
═════════════════════════════════════════════════════════════════
Exit code: 0
```

### 5. Explanation
By default, LiteMigrate forbids silent data destruction. When `drop_table.sql` dropped `orders`, LiteMigrate aborted promotion with exit code `1` and left `demo2.db` intact. Once the operator explicitly authorized the drop in `allow_drop_policy.json`, validation succeeded.

---

## Scenario 3: Foreign-Key Cascade Scenario

### Objective
Demonstrate that deleting parent rows that causes orphaned child rows or cascade deletions is detected and rejected by post-migration foreign key checks.

### 1. Setup Instructions
```bash
mkdir -p /tmp/litemigrate_demo_s3 && cd /tmp/litemigrate_demo_s3

python3 -c '
import sqlite3
con = sqlite3.connect("demo3.db")
con.execute("PRAGMA foreign_keys = ON;")
con.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT)")
con.execute("CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id), note TEXT)")
con.execute("INSERT INTO parent VALUES (1, \"Parent 1\")")
con.execute("INSERT INTO child VALUES (10, 1, \"Child of 1\")")
con.commit()
con.close()
'
```

### 2. Migration SQL (`delete_parent.sql`)
```sql
DELETE FROM parent WHERE id = 1;
```

### 3. Exact CLI Commands
```bash
litemigrate validate --db demo3.db --migration delete_parent.sql
```

### 4. Actual CLI Output
```text
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — VALIDATE
═════════════════════════════════════════════════════════════════
  Verdict:               BLOCKED_FOREIGN_KEY_VIOLATION
  Source Database:       /tmp/litemigrate_demo_s3/demo3.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.55 ms
  Migration Execution:   0.47 ms
  Audit Duration:        0.23 ms
  Total Elapsed Time:    3.27 ms

  Audit Findings & Details:
    • Table 'child' rowid 10 violates foreign key constraint #0 referencing parent 'parent'

  Foreign Key Violations:
    ✗ Table 'child' rowid 10 violates foreign key constraint #0 referencing parent 'parent'
═════════════════════════════════════════════════════════════════
Exit code: 1
```

### 5. Explanation
In SQLite, executing DDL statements often disables foreign keys during 12-step table rebuilds. However, LiteMigrate re-enforces `PRAGMA foreign_key_check` across all tables on the shadow database before any promotion can occur. Deleting `parent` left `child` referencing an orphaned ID, immediately halting promotion.

---

## Scenario 4: Invalid Foreign-Key Migration (Orphan Insertion)

### Objective
Demonstrate that inserting records with invalid foreign keys into populated tables is caught on the shadow sandbox before live data is compromised.

### 1. Setup Instructions
```bash
mkdir -p /tmp/litemigrate_demo_s4 && cd /tmp/litemigrate_demo_s4

python3 -c '
import sqlite3
con = sqlite3.connect("demo4.db")
con.execute("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT)")
con.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, category_id INTEGER REFERENCES categories(id), name TEXT)")
con.execute("INSERT INTO categories VALUES (1, \"Electronics\")")
con.commit()
con.close()
'
```

### 2. Migration SQL (`insert_orphan.sql`)
```sql
INSERT INTO products (id, category_id, name) VALUES (101, 999, 'Phantom Widget');
```

### 3. Exact CLI Commands
```bash
litemigrate validate --db demo4.db --migration insert_orphan.sql
```

### 4. Actual CLI Output
```text
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — VALIDATE
═════════════════════════════════════════════════════════════════
  Verdict:               BLOCKED_FOREIGN_KEY_VIOLATION
  Source Database:       /tmp/litemigrate_demo_s4/demo4.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.42 ms
  Migration Execution:   0.46 ms
  Audit Duration:        0.24 ms
  Total Elapsed Time:    2.79 ms

  Audit Findings & Details:
    • Table 'products' rowid 101 violates foreign key constraint #0 referencing parent 'categories'

  Foreign Key Violations:
    ✗ Table 'products' rowid 101 violates foreign key constraint #0 referencing parent 'categories'
═════════════════════════════════════════════════════════════════
Exit code: 1
```

### 5. Explanation
Because `category_id 999` does not exist in `categories`, `PRAGMA foreign_key_check` flags the violation on `products` rowid 101. The source database `demo4.db` remains 100% untouched.

---

## Scenario 5: Concurrent Source Modification (CAS Protection)

### Objective
Demonstrate that if an external process modifies the source SQLite database while shadow validation is running, LiteMigrate's Compare-And-Swap (CAS) mechanism detects the mutation and cleanly aborts promotion to prevent lost updates.

### 1. Setup Instructions
```bash
mkdir -p /tmp/litemigrate_demo_s5 && cd /tmp/litemigrate_demo_s5

python3 -c '
import sqlite3
con = sqlite3.connect("demo5.db")
con.execute("PRAGMA journal_mode = WAL;")
con.execute("CREATE TABLE counter (id INTEGER PRIMARY KEY, count INTEGER)")
con.execute("INSERT INTO counter VALUES (1, 100)")
con.commit()
con.close()
'
```

### 2. Python Reproduction Script (`test_concurrency.py`)
```python
import sqlite3
from pathlib import Path
from litemigrate.cloning import create_shadow_database
from litemigrate.fingerprint import compute_logical_db_digest
from litemigrate.promotion import promote_shadow_to_source
from litemigrate.sqlite_backend import open_hardened_sqlite

db_path = Path("demo5.db")

# Step 1: Clone shadow database and compute baseline digest
clone_res = create_shadow_database(db_path)
shadow_conn = open_hardened_sqlite(clone_res.shadow_path)
baseline_digest = compute_logical_db_digest(shadow_conn)
shadow_conn.close()

# Step 2: Simulate concurrent writer committing to source database!
writer_conn = sqlite3.connect(db_path)
writer_conn.execute("UPDATE counter SET count = 200 WHERE id = 1;")
writer_conn.commit()
writer_conn.close()

# Step 3: Attempt promotion with stale baseline digest
try:
    promote_shadow_to_source(
        shadow_path=clone_res.shadow_path,
        source_path=db_path,
        expected_source_digest=baseline_digest,
        migration_sql="ALTER TABLE counter ADD COLUMN extra TEXT;",
    )
except Exception as exc:
    print(f"Promotion Aborted: {type(exc).__name__}: {exc}")
```

### 3. Exact CLI Command
```bash
python3 test_concurrency.py
```

### 4. Actual CLI Output
```text
Promotion Aborted: ConcurrencyConflictError: Source database was modified by a concurrent writer prior to promotion lock acquisition; aborting to prevent lost updates.
```

### 5. Explanation
Under `BEGIN IMMEDIATE`, LiteMigrate re-computes `PRAGMA data_version` and the logical database digest of the live source database. Because `count` was updated from `100` to `200` while validation took place, the digests did not match. Promotion immediately aborted, preserving the concurrent write and preventing data loss.

---

## Scenario 6: Validation Report Generation & Inspection

### Objective
Demonstrate generating a machine-readable JSON audit report from a validation run and inspecting it using `litemigrate report`.

### 1. Setup Instructions & Migration
```bash
mkdir -p /tmp/litemigrate_demo_s6 && cd /tmp/litemigrate_demo_s6

python3 -c '
import sqlite3
con = sqlite3.connect("demo6.db")
con.execute("CREATE TABLE inventory (sku TEXT PRIMARY KEY, qty INT)")
con.execute("INSERT INTO inventory VALUES (\"WIDGET-01\", 50)")
con.commit()
con.close()
'

cat << 'EOF' > update_schema.sql
ALTER TABLE inventory ADD COLUMN reorder_level INT DEFAULT 10;
CREATE INDEX idx_reorder ON inventory(reorder_level);
EOF
```

### 2. Exact CLI Commands
```bash
# Step A: Validate and write JSON report to disk
litemigrate validate --db demo6.db --migration update_schema.sql --output audit_report.json

# Step B: Format and display the saved report
litemigrate report --input audit_report.json
```

### 3. Actual CLI Output
```text
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — REPORT
═════════════════════════════════════════════════════════════════
  Verdict:               PASSED
  Source Database:       /tmp/litemigrate_demo_s6/demo6.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.34 ms
  Migration Execution:   0.45 ms
  Audit Duration:        0.22 ms
  Total Elapsed Time:    2.80 ms

  Audit Findings & Details:
    • Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.
═════════════════════════════════════════════════════════════════
```

### 4. Output JSON Excerpt (`audit_report.json`)
```json
{
  "verdict": "passed",
  "details": [
    "Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied."
  ],
  "original_db_path": "/tmp/litemigrate_demo_s6/demo6.db",
  "original_db_sha256_before": "426f4f107380cfd6fcddba572d4ff9272338cb8c962b921fa25d3faad52a3ee5",
  "original_db_sha256_after": "426f4f107380cfd6fcddba572d4ff9272338cb8c962b921fa25d3faad52a3ee5",
  "original_db_untouched": true,
  "promoted_to_source": false,
  "backup_path": null,
  "clone_result": {
    "shadow_path": "/var/folders/.../demo6.shadow.db",
    "strategy_used": "apfs_clonefile",
    "duration_ms": 0.34,
    "wal_required_backup_fallback": false,
    "wal_size_bytes_at_clone": 0,
    "notes": ["Created shadow database via macOS APFS clonefile(2)."]
  }
}
```

### 5. Explanation
The complete audit state is captured as structured JSON. This report can be preserved as an auditable compliance artifact or ingested by CI/CD pipelines to fail deployments if the verdict is anything other than `passed`.
