# LiteMigrate — Technical Demo Video Scripts & Terminal Recordings

This document provides exact recording scripts for producing short, high-impact technical demonstrations (suitable for Asciinema recordings, GitHub README GIF embeds, and short-form developer videos).

---

## Recording Environment Guidelines

- **Terminal Size**: 88 columns × 28 rows (standard high-legibility layout).
- **Font**: JetBrains Mono or Fira Code, 16pt.
- **Theme**: Dark mode (Slate / Monokai / Tokyo Night).
- **Prompt**: Minimal prompt, e.g. `➜ ~/dev/demo $ `.
- **Tool**: `asciinema` or `vhs` (Charm).

---

## Script 1: The 60-Second Hook — "Catching a Silent Data Loss Bug"

**Theme**: A developer runs an innocent-looking table rebuild that would destroy production data, but LiteMigrate catches it in 3 milliseconds.  
**Length**: 45–60 seconds.

```text
[00:00 - 00:05]
# VISUAL: Terminal is clear. 
# Prompt:
➜ ~/demo $ ls -l
-rw-r--r-- 1 dev dev 24576 Nov 10 17:00 production_users.db
-rw-r--r-- 1 dev dev   182 Nov 10 17:01 rebuild_teams.sql

[00:05 - 00:15]
# ACTION: Inspect the migration script.
➜ ~/demo $ cat rebuild_teams.sql
-- Table rebuild: drop parent teams table to change a constraint
DROP TABLE teams;
CREATE TABLE teams (id INT PRIMARY KEY, name TEXT, tier TEXT DEFAULT 'free');

[00:15 - 00:25]
# SUBTITLE: In SQLite, foreign key cascades can silently wipe all child rows in `team_members`!
# NARRATION: "What happens if we execute this directly on our database?"

[00:25 - 00:40]
# ACTION: Run LiteMigrate validate against the database.
➜ ~/demo $ litemigrate validate --db production_users.db --migration rebuild_teams.sql

# TERMINAL OUTPUT:
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — VALIDATE
═════════════════════════════════════════════════════════════════
  Verdict:               BLOCKED_FOREIGN_KEY_VIOLATION
  Source Database:       production_users.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.38 ms
  Migration Execution:   0.45 ms
  Audit Duration:        0.21 ms
  Total Elapsed Time:    2.85 ms

  Audit Findings & Details:
    • Table 'team_members' rowid 101 violates foreign key constraint #0 referencing parent 'teams'

  Foreign Key Violations:
    ✗ Table 'team_members' rowid 101 violates foreign key constraint #0 referencing parent 'teams'
═════════════════════════════════════════════════════════════════

[00:40 - 00:55]
# SUBTITLE: Caught in 2.8 milliseconds. production_users.db was never touched.
# ACTION: Verify database is intact.
➜ ~/demo $ sqlite3 production_users.db "SELECT count(*) FROM team_members;"
14,280

[00:55 - 01:00]
# CALL TO ACTION (Text card):
"Test before you migrate. Validate first. Promote safely."
LiteMigrate — Open source at github.com/chiragjangiir/litemigrate
```

---

## Script 2: Sub-Millisecond Shadow Cloning Explained

**Theme**: Showing how copy-on-write reflinks create isolated sandboxes with zero performance overhead.  
**Length**: 45 seconds.

```text
[00:00 - 00:10]
# VISUAL: Display a 500MB SQLite database.
➜ ~/benchmark $ ls -lh large_catalog.db
-rw-r--r-- 1 dev dev 512M Nov 10 17:05 large_catalog.db

[00:10 - 00:25]
# ACTION: Run validation on the 512MB database.
➜ ~/benchmark $ litemigrate validate --db large_catalog.db --migration 001_add_sku_index.sql

# TERMINAL OUTPUT:
═════════════════════════════════════════════════════════════════
 LiteMigrate Audit Report — VALIDATE
═════════════════════════════════════════════════════════════════
  Verdict:               PASSED
  Source Database:       large_catalog.db
  Promoted to Source:    No
  Source DB Untouched:   Yes
  Clone Strategy Used:   apfs_clonefile
  Clone Duration:        0.41 ms
  Migration Execution:   84.2 ms
  Audit Duration:        12.1 ms
  Total Elapsed Time:    98.3 ms
═════════════════════════════════════════════════════════════════

[00:25 - 00:40]
# SUBTITLE: 512MB database cloned in 0.41 milliseconds using filesystem copy-on-write.
# NARRATION: "Zero extra disk space allocated until pages are modified. Zero risk to production."

[00:40 - 00:45]
# CALL TO ACTION:
LiteMigrate — Local-first SQLite migration safety.
github.com/chiragjangiir/litemigrate
```

---

## Script 3: Concurrency-Safe Promotion (CAS)

**Theme**: Demonstrating how Compare-And-Swap prevents lost updates in multi-process SQLite environments.  
**Length**: 60 seconds.

```text
[00:00 - 00:15]
# VISUAL: Split terminal.
# Left pane: LiteMigrate migration.
# Right pane: Active web application or worker process.

[00:15 - 00:30]
# ACTION: Left pane validates migration.
[Left]  ➜ ~/app $ litemigrate validate --db app.db --migration alter_users.sql
[Left]  Verdict: PASSED

[00:30 - 00:42]
# ACTION: Right pane simulates concurrent user registration while migration prepares to apply!
[Right] ➜ ~/app $ python3 -c "import sqlite3; c=sqlite3.connect('app.db'); c.execute('INSERT INTO users VALUES (99, \"new@user.com\")'); c.commit()"
[Right] Committed 1 row to app.db.

[00:42 - 00:55]
# ACTION: Left pane attempts to apply!
[Left]  ➜ ~/app $ litemigrate apply --db app.db --migration alter_users.sql --confirm
[Left]  ═════════════════════════════════════════════════════════════════
[Left]   Verdict:               BLOCKED_CONCURRENT_MUTATION
[Left]   Source Database:       app.db
[Left]   Source DB Untouched:   Yes
[Left]   Details:
[Left]     • Source database was modified by a concurrent writer prior to promotion lock acquisition; aborting to prevent lost updates.
[Left]  ═════════════════════════════════════════════════════════════════

[00:55 - 01:00]
# SUBTITLE: Promotion cleanly aborted. Zero lost updates.
github.com/chiragjangiir/litemigrate
```
