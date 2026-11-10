# LiteMigrate — Safety Model & Invariant Policy

LiteMigrate treats database migrations with strict defensive defaults. A migration is never assumed to be safe simply because its SQL statements executed without raising a syntax error.

## The Verdict Model

LiteMigrate produces explicit, structured verdicts:

| Verdict | Cause | Action Taken |
| :--- | :--- | :--- |
| `PASSED` | All schema, data, foreign key, and integrity invariants satisfied. | Migration may be safely applied. |
| `BLOCKED_UNEXPECTED_TABLE_DROP` | A table was dropped that was not in `policy.allowed_dropped_tables`. | Promotion blocked; source untouched. |
| `BLOCKED_UNEXPECTED_ROW_LOSS` | A table lost rows without declaration in `policy.allowed_row_loss_tables`. | Promotion blocked; source untouched. |
| `BLOCKED_UNEXPECTED_DATA_MUTATION` | Table content modified without declaration in `policy.allowed_mutated_tables`. | Promotion blocked; source untouched. |
| `BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP` | A view, trigger, or index was dropped without policy allowlisting. | Promotion blocked; source untouched. |
| `BLOCKED_FOREIGN_KEY_VIOLATION` | An orphan row or broken reference detected by `PRAGMA foreign_key_check`. | Promotion blocked; source untouched. |
| `BLOCKED_INTEGRITY_FAILURE` | SQLite B-tree or surviving view corruption detected by integrity check. | Promotion blocked; source untouched. |
| `BLOCKED_MIGRATION_EXCEPTION` | Migration SQL execution failed on the shadow database. | Shadow rolled back; source untouched. |
| `BLOCKED_CONCURRENT_LOCK` | Database or lockfile locked beyond configured `busy_timeout_ms`. | Promotion aborted; source untouched. |
| `BLOCKED_SOURCE_MODIFIED_CONCURRENTLY` | Source database was modified by external writer during validation. | Promotion rolled back; external write preserved! |
| `BLOCKED_UNSUPPORTED_MIGRATION_TYPE` | Non-SQL migration (e.g., Python callable) supplied. | Rejected immediately; source untouched. |

## Why Policy Declarations Are Required

In production SQLite databases, destructive changes frequently happen by accident:
1. **Foreign Key Cascade Wipes ([ariga/atlas #3317](https://github.com/ariga/atlas/issues/3317)):** Dropping a parent table while `foreign_keys=ON` cascades to child tables, wiping thousands of rows without any warning.
2. **Table Rebuild Mistakes:** In SQLite's 12-step table rebuild, copying data via `INSERT INTO t_new SELECT ... FROM t_old` with mismatched columns silently sets columns to `NULL` or default values.
3. **Trigger Invalidation:** Renaming a table can leave surviving triggers or views referencing non-existent identifiers.

By requiring explicit declarations in `MigrationPolicy`, LiteMigrate guarantees that intentional deletions are authorized while unintentional bugs are caught immediately.
