# SQLite Schema Migration Cookbook

## 1. Zero-Downtime Column Addition
SQLite supports `ALTER TABLE ADD COLUMN` safely for columns with `NULL` or constant `DEFAULT` values without table rewrites.

## 2. Table Rewrites with Foreign Keys
When modifying column types or dropping columns in SQLite versions prior to 3.35:
1. Disable foreign keys (`PRAGMA foreign_keys = OFF;`).
2. Create new table `target_new`.
3. Copy data `INSERT INTO target_new SELECT ... FROM target`.
4. Drop old table and rename `target_new` to `target`.
5. Run `PRAGMA foreign_key_check;`.
6. Re-enable foreign keys (`PRAGMA foreign_keys = ON;`).
