# Zero-Downtime SQLite Migration Patterns

This guide documents proven patterns for executing non-blocking schema modifications in production SQLite.

---

## 1. Safe Column Rename Pattern
1. Create new table with updated column name.
2. Bulk copy existing records with column projection.
3. Drop legacy table.
4. Rename new table to original identifier.
