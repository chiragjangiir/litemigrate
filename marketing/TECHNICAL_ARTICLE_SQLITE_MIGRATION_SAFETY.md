# Why Successful SQL Execution Does Not Guarantee a Safe Migration

In modern software development, most database migration frameworks operate on a simple assumption:  
**If the migration script executes without raising an exception, the migration succeeded.**

If you are using PostgreSQL or MySQL, this assumption is usually reasonable—DDL statements either succeed atomically or roll back with a descriptive error.

**In SQLite, this assumption is dangerously false.**

Because of SQLite's lightweight architecture, dynamic typing, and limited `ALTER TABLE` capabilities, a migration script can execute with **exit code 0** while silently destroying data, dropping columns, wiping related tables, or introducing corrupt page states.

In this deep-dive article, we examine the four primary failure modes of SQLite migrations and explain why invariant verification is necessary.

---

## 1. The Foreign Key Cascade Annihilation

SQLite did not support foreign keys in its initial design. Even today, foreign key enforcement is turned off by default unless explicitly activated via `PRAGMA foreign_keys = ON;`.

When foreign keys *are* enabled, `ON DELETE CASCADE` creates a hazardous failure mode:

```sql
-- Assume users (parent) and api_tokens (child, ON DELETE CASCADE)
-- A developer attempts to "refresh" an old user record during a migration:
DELETE FROM users WHERE last_login < '2023-01-01';
```

If `api_tokens` references `users(id)` with `ON DELETE CASCADE`, SQLite silently purges every token belonging to those users. No warning is printed. No error is raised.

Even worse: during a **table rebuild** (which SQLite frequently requires), developers often write:
```sql
PRAGMA foreign_keys = OFF;
CREATE TABLE users_new (...);
INSERT INTO users_new SELECT * FROM users;
DROP TABLE users;  -- What happens to child tables?
ALTER TABLE users_new RENAME TO users;
PRAGMA foreign_keys = ON;
```
If you forget to re-enable foreign keys or re-validate foreign keys using `PRAGMA foreign_key_check;`, orphan rows accumulate silently. Future queries will fail or return corrupted joins.

---

## 2. The 12-Step Rebuild Trap: Silent Column Dropping

SQLite supports adding a column (`ALTER TABLE ... ADD COLUMN`) and renaming a table or column. However, it **does not support**:
- Dropping a column (in SQLite versions < 3.35.0).
- Altering column data types.
- Adding or dropping `CHECK` constraints.
- Modifying primary keys or foreign key actions.

To make these changes, SQLite's official documentation prescribes the **12-step table rebuild procedure**:

```
Step 1:  BEGIN TRANSACTION
Step 2:  PRAGMA foreign_keys = OFF
Step 3:  CREATE TABLE new_table (...)
Step 4:  INSERT INTO new_table SELECT ... FROM old_table
Step 5:  DROP TABLE old_table
Step 6:  ALTER TABLE new_table RENAME TO old_table
Step 7:  Re-create indexes, triggers, and views
Step 8:  PRAGMA foreign_key_check
Step 9:  COMMIT
Step 10: PRAGMA foreign_keys = ON
```

### Where it goes wrong:
Consider Step 4. If the developer writes:
```sql
INSERT INTO orders_new (order_id, user_id, amount)
SELECT order_id, user_id, amount FROM orders;
```
If the original `orders` table had a fourth column (`discount_code` or `tax_rate`), and the developer forgot to include it in the `SELECT` list, **the rebuild executes cleanly, the old table is dropped, and the fourth column is permanently lost.**

No error was generated. The migration runner checked the exit status, saw `0`, and recorded that the migration passed.

---

## 3. Dynamic Typing & Storage Class Discrepancies

Unlike strict RDBMSs, SQLite uses type affinity. A column declared as `INTEGER` will cheerfully store text, floating-point numbers, or binary BLOBs unless the table was declared with the `STRICT` table option (introduced in SQLite 3.37.0).

During migrations that reshape data:
```sql
UPDATE transactions SET fee = fee / 100;
```
If `fee` was previously an integer representing cents, dividing by 100 converts the column affinity to floating-point. In standard IEEE-754 arithmetic, values like `0.0` and `-0.0` have distinct binary representations. If downstream code expects integer representations or strict hashing, queries behave unpredictably.

---

## 4. Concurrent Clobbering (The Lost Update Problem)

SQLite is a single-writer database. In concurrent multi-process environments (such as a Gunicorn / Uvicorn Python application or worker queues reading and writing to an SQLite database):

1. The migration script connects and begins validating.
2. A web worker receives an HTTP request and commits a new user row to `app.db`.
3. The migration script finishes and replaces the database file or executes a batch of DDL that overrides the newly inserted row.

Standard migration runners have no concept of Compare-And-Swap (CAS) validation. If an out-of-band write occurs, the migration runner simply acquires a lock whenever it is available, unaware that the data state shifted beneath it.

---

## The Solution: Multi-Invariant Shadow Verification

To verify that a migration satisfies essential database invariants before touching real data, a migration tool must do more than run SQL. It must verify **behavioral invariants**:

| Invariant | How LiteMigrate Verifies It |
|:---|:---|
| **Zero Accidental Row Loss** | Pre- and post-migration streaming row fingerprinting across all tables. |
| **Relational Integrity** | Automated execution of `PRAGMA foreign_key_check;` across the entire schema. |
| **Physical Page Integrity** | Automated `PRAGMA integrity_check;` on the migrated database. |
| **Schema Object Continuity** | Snapshot comparison of all views, triggers, and indexes. |
| **No Concurrent Lost Updates** | Atomic Compare-And-Swap (CAS) verification via `PRAGMA data_version` under `BEGIN IMMEDIATE`. |
| **Isolated Execution** | Execution takes place on an isolated copy-on-write shadow copy; source database remains 100% untouched until promotion. |

---

## Conclusion

In SQLite, syntax validity is not safety. A migration is only safe when you can prove that:
1. Every existing row survived intact.
2. No undeclared columns were truncated.
3. All foreign key relationships hold.
4. The database physical pages are clean.
5. The live database was not modified concurrently.

This is why we built **LiteMigrate**: to bring deterministic, local-first safety verification to SQLite.

- **GitHub**: [https://github.com/chiragjangiir/litemigrate](https://github.com/chiragjangiir/litemigrate)  
- **Current Release**: `v0.1.0-alpha.1` (Experimental Alpha)

