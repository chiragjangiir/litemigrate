# LiteMigrate — Demonstration Recording Plan & Technical Screencast Guide

**Current Asset Status**: As of `v0.1.0-alpha.1`, **no finished video (`.mp4`), screencast (`.cast`), or animated GIF currently exists in the repository.**

This document provides the definitive, turn-key recording specification to produce the official demonstration recording (e.g. for `vhs`, `asciinema`, or terminal screencasting).

---

## Technical Recording Specifications

- **Tool Recommendation**: [VHS (Charm)](https://github.com/charmbracelet/vhs) or [Asciinema](https://asciinema.org/).
- **Output Artifacts**:
  - `docs/assets/litemigrate_demo.gif` (for GitHub README header, max 4MB).
  - `docs/assets/litemigrate_demo.mp4` (high-res 1080p 60fps for social/Hacker News).
- **Terminal Resolution**: 1200 × 750 px (approx. 90 columns × 26 rows).
- **Font**: JetBrains Mono, 15pt.
- **Color Theme**: Dracula or Catppuccin Mocha.
- **Typing Speed**: Realistic human simulation (40ms jitter).
- **Total Duration**: Approximately 75 seconds.

---

## 7-Scene Demonstration Storyboard

```
Scene 1: Disposable Database Setup (00:00 - 00:10)
Scene 2: Show Migration SQL (00:10 - 00:18)
Scene 3: Run `litemigrate inspect` (00:18 - 00:28)
Scene 4: Run `litemigrate validate` (00:28 - 00:40)
Scene 5: Inspect Validation Report (00:40 - 00:50)
Scene 6: Demonstrate Blocked Destructive Migration (00:50 - 01:05)
Scene 7: Why Validation Precedes Promotion (01:05 - 01:15)
```

---

### Scene 1: Show a Disposable SQLite Database (00:00 - 00:10)
- **Narration / Subtitle**: "We start with a populated, disposable SQLite database."
- **Terminal Command**:
  ```bash
  sqlite3 store.db "SELECT count(*) FROM products; SELECT count(*) FROM orders;"
  ```
- **Actual Expected Output**:
  ```text
  1250
  4820
  ```
- **Visual Cue**: Clear terminal, quick count verification confirming populated tables.

---

### Scene 2: Show the Migration SQL (00:10 - 00:18)
- **Narration / Subtitle**: "Here is our migration script adding a column and an index."
- **Terminal Command**:
  ```bash
  cat 001_add_inventory.sql
  ```
- **Actual Expected Output**:
  ```sql
  ALTER TABLE products ADD COLUMN warehouse_bin TEXT DEFAULT 'A-01';
  CREATE INDEX idx_products_bin ON products(warehouse_bin);
  ```

---

### Scene 3: Run `litemigrate inspect` (00:18 - 00:28)
- **Narration / Subtitle**: "First, inspect the schema structure, journal mode, and integrity."
- **Terminal Command**:
  ```bash
  litemigrate inspect --db store.db
  ```
- **Actual Expected Output**:
  ```text
  ═════════════════════════════════════════════════════════════════
   LiteMigrate — Database Inspection Report
  ═════════════════════════════════════════════════════════════════
    Database Path:         store.db
    SQLite Version:        3.43.2
    Journal Mode:          WAL
    File Size:             245,760 bytes
    Table Count:           2
    Schema Objects:        2
    Foreign Keys Enabled:  Yes
    Database Integrity:    PASSED

    User Tables:
      • orders
      • products
  ═════════════════════════════════════════════════════════════════
  ```

---

### Scene 4: Run `litemigrate validate` (00:28 - 00:40)
- **Narration / Subtitle**: "Now validate the migration. This runs in a copy-on-write shadow sandbox—the source database is never modified."
- **Terminal Command**:
  ```bash
  litemigrate validate --db store.db --migration 001_add_inventory.sql --output report.json
  ```
- **Actual Expected Output**:
  ```text
  ═════════════════════════════════════════════════════════════════
   LiteMigrate Audit Report — VALIDATE
  ═════════════════════════════════════════════════════════════════
    Verdict:               PASSED
    Source Database:       store.db
    Promoted to Source:    No
    Source DB Untouched:   Yes
    Clone Strategy Used:   apfs_clonefile
    Clone Duration:        0.34 ms
    Migration Execution:   0.62 ms
    Audit Duration:        0.41 ms
    Total Elapsed Time:    3.15 ms

    Audit Findings & Details:
      • Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.
  ═════════════════════════════════════════════════════════════════
  ```

---

### Scene 5: Show the Validation Report (00:40 - 00:50)
- **Narration / Subtitle**: "LiteMigrate provides an auditable, machine-readable JSON report of all invariant checks."
- **Terminal Command**:
  ```bash
  litemigrate report --input report.json
  ```
- **Actual Expected Output**:
  ```text
  ═════════════════════════════════════════════════════════════════
   LiteMigrate Audit Report — REPORT
  ═════════════════════════════════════════════════════════════════
    Verdict:               PASSED
    Source Database:       store.db
    Promoted to Source:    No
    Source DB Untouched:   Yes
    Clone Strategy Used:   apfs_clonefile
    Clone Duration:        0.34 ms
    Migration Execution:   0.62 ms
    Audit Duration:        0.41 ms
    Total Elapsed Time:    3.15 ms

    Audit Findings & Details:
      • Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.
  ═════════════════════════════════════════════════════════════════
  ```

---

### Scene 6: Demonstrate a Destructive Migration Being Blocked (00:50 - 01:05)
- **Narration / Subtitle**: "What if a migration accidentally drops a table or causes row loss? LiteMigrate blocks it immediately."
- **Terminal Command**:
  ```bash
  echo "DROP TABLE orders;" > bad_migration.sql
  litemigrate validate --db store.db --migration bad_migration.sql
  ```
- **Actual Expected Output**:
  ```text
  ═════════════════════════════════════════════════════════════════
   LiteMigrate Audit Report — VALIDATE
  ═════════════════════════════════════════════════════════════════
    Verdict:               BLOCKED_UNEXPECTED_TABLE_DROP
    Source Database:       store.db
    Promoted to Source:    No
    Source DB Untouched:   Yes
    Clone Strategy Used:   apfs_clonefile
    Clone Duration:        0.32 ms
    Migration Execution:   0.41 ms
    Audit Duration:        0.08 ms
    Total Elapsed Time:    2.15 ms

    Audit Findings & Details:
      • Unexpected dropped table 'orders' was not declared in policy.allowed_dropped_tables.

    Dropped Tables:        orders
  ═════════════════════════════════════════════════════════════════
  ```
- **Visual Cue**: Red/Amber warning highlight on `BLOCKED_UNEXPECTED_TABLE_DROP` and explicit verification that `store.db` was untouched.

---

### Scene 7: Explain Why Validation Happens Before Promotion (01:05 - 01:15)
- **Narration / Subtitle**: "In SQLite, syntax success is not safety. Validate first. Promote safely."
- **Terminal Command (Applying Validated Migration)**:
  ```bash
  litemigrate apply --db store.db --migration 001_add_inventory.sql --confirm
  ```
- **Actual Expected Output**:
  ```text
  ═════════════════════════════════════════════════════════════════
   LiteMigrate Audit Report — APPLY
  ═════════════════════════════════════════════════════════════════
    Verdict:               PASSED
    Source Database:       store.db
    Promoted to Source:    Yes
    Source DB Untouched:   No
    Pre-Promote Backup:    store.db.pre_migrate_1794311745.bak
    Total Elapsed Time:    6.85 ms
  ═════════════════════════════════════════════════════════════════
  ```
- **Closing Card**:
  ```text
  LiteMigrate — Open source local-first SQLite migration safety.
  github.com/chiragjangiir/litemigrate
  ```

---

## Automated VHS Tape Configuration (`demo.tape`)

Developers with `vhs` installed can compile the entire recording autonomously with this tape:

```text
Output docs/assets/litemigrate_demo.gif
Output docs/assets/litemigrate_demo.mp4

Set FontSize 15
Set Width 1200
Set Height 750
Set Theme "Catppuccin Mocha"
Set Padding 20

Type "litemigrate inspect --db store.db" Sleep 500ms Enter Sleep 3s
Type "litemigrate validate --db store.db --migration 001_add_inventory.sql" Sleep 500ms Enter Sleep 3s
Type "litemigrate validate --db store.db --migration bad_migration.sql" Sleep 500ms Enter Sleep 3s
Type "litemigrate apply --db store.db --migration 001_add_inventory.sql --confirm" Sleep 500ms Enter Sleep 4s
```
