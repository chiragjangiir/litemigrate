# Tester Quickstart Guide (5-Minute Walkthrough)

This guide walks you through setting up and testing **LiteMigrate Alpha (`v0.1.0-alpha.1`)** in less than 5 minutes using a completely disposable SQLite database.

---

## 1. Prerequisites & Installation

LiteMigrate requires **Python 3.10+** and uses the standard library `sqlite3` engine.

```bash
# Create and activate an isolated virtual environment
mkdir litemigrate-test && cd litemigrate-test
python3 -m venv .venv
source .venv/bin/activate

# Install the published Alpha wheel from GitHub Releases
curl -sLO https://github.com/chiragjangiir/litemigrate/releases/download/v0.1.0-alpha.1/litemigrate-0.1.0a1-py3-none-any.whl
pip install litemigrate-0.1.0a1-py3-none-any.whl

# Verify version
litemigrate --version
# Output: litemigrate 0.1.0a1
```

---

## 2. Create a Disposable Database

Generate a quick SQLite database with realistic initial data:

```bash
python3 -c '
import sqlite3

con = sqlite3.connect("ecommerce_test.db")
con.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        signup_date TEXT NOT NULL
    );
""")
con.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
        amount REAL NOT NULL,
        status TEXT DEFAULT "pending"
    );
""")

con.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", [
    (1, "Alice Smith", "alice@example.com", "2026-01-10"),
    (2, "Bob Jones", "bob@example.com", "2026-02-15"),
    (3, "Carol White", "carol@example.com", "2026-03-01"),
])

con.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", [
    (101, 1, 99.50, "completed"),
    (102, 1, 14.99, "pending"),
    (103, 2, 250.00, "completed"),
])

con.commit()
con.close()
print("Created disposable database: ecommerce_test.db")
'
```

---

## 3. Core Commands Walkthrough

### A. Inspect Schema & Data Footprint
Inspect tables, row counts, indexes, foreign keys, and pragmas:
```bash
litemigrate inspect --db ecommerce_test.db
```
To output machine-readable JSON:
```bash
litemigrate inspect --db ecommerce_test.db --json
```

---

### B. Validate a Safe Migration (Non-Destructive)
Create a migration script adding a column and an index:
```bash
cat << 'EOF' > v1_add_loyalty.sql
-- Add column with default value
ALTER TABLE customers ADD COLUMN loyalty_tier TEXT DEFAULT 'bronze';

-- Add index on foreign key column
CREATE INDEX idx_orders_customer ON orders(customer_id);
EOF
```

Run `validate`. **This runs on an isolated shadow clone and leaves `ecommerce_test.db` completely untouched:**
```bash
litemigrate validate --db ecommerce_test.db --migration v1_add_loyalty.sql --output audit_report.json
```
*Note that the exit code is `0`, the shadow clone execution succeeded, and foreign key / integrity checks passed.*

---

### C. Apply Migration with Atomic Backup
To apply changes to the live database, run `apply` with `--confirm`:
```bash
litemigrate apply --db ecommerce_test.db --migration v1_add_loyalty.sql --confirm
```
**What happens under the hood:**
1. Shadow clone is created and validated.
2. A pre-migration backup (`ecommerce_test.db.pre_migrate_<timestamp>.bak`) is created atomically using the SQLite Backup API.
3. Concurrency check (CAS) ensures no external process modified the source while validation took place.
4. Changes are committed to `ecommerce_test.db`.

---

### D. Export and View an Audit Report
Format and inspect the JSON audit report:
```bash
litemigrate report --input audit_report.json
```

---

## 4. What Happens When Validation Fails?

### Case 1: Foreign Key Violation
Create a migration script that violates foreign keys:
```bash
cat << 'EOF' > invalid_fk.sql
PRAGMA foreign_keys = ON;
-- Insert an order with non-existent customer_id 999
INSERT INTO orders (order_id, customer_id, amount, status) VALUES (104, 999, 45.00, 'pending');
EOF
```

Run validate:
```bash
litemigrate validate --db ecommerce_test.db --migration invalid_fk.sql
```
**Result:**
- Validation aborts with exit code `1`.
- `BLOCKED_FOREIGN_KEY_VIOLATION` is reported.
- `ecommerce_test.db` remains untouched.

---

### Case 2: Destructive Migration Without Policy Flag
Create a destructive script:
```bash
cat << 'EOF' > drop_orders.sql
DROP TABLE orders;
EOF
```

Run validate without flags:
```bash
litemigrate validate --db ecommerce_test.db --migration drop_orders.sql
```
**Result:**
- Rejection: Unexpected dropped table `orders` was not declared in policy.
- Verdict: `BLOCKED_UNEXPECTED_TABLE_DROP` (Exit code `1`).

To explicitly permit it:
```bash
cat << 'EOF' > allow_drop.json
{
  "allowed_dropped_tables": ["orders"],
  "allowed_row_loss_tables": ["orders"]
}
EOF

litemigrate validate --db ecommerce_test.db --migration drop_orders.sql --policy allow_drop.json
```

---

## 5. Cleaning Up

Since this is a disposable test, simply remove the test files:
```bash
rm -f ecommerce_test.db* *.sql *.json
deactivate
```

