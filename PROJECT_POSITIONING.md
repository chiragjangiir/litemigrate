# LiteMigrate — Project Positioning & Messaging Architecture

> **"Test before you migrate. Validate first. Promote safely."**

LiteMigrate is a local-first SQLite migration safety utility that validates migrations against an isolated copy-on-write shadow database before promoting them to your source database.

---

## 1. Target Audiences

LiteMigrate is engineered specifically for three distinct developer groups who interact with SQLite in critical paths:

### A. Python Developers & Application Engineers
- **Profile**: Developers building applications using Django, FastAPI, Flask, SQLAlchemy, Peewee, Tortoise, Litestar, or the standard library `sqlite3`.
- **Pain Point**: SQLite table alteration constraints often require multi-step table rebuilds (creating a temporary table, copying rows, dropping the old table, renaming). A single misconfigured foreign key cascade or dropped column causes silent, irreversible data loss.
- **Value**: Run migrations inside an isolated shadow database first. Verify that row counts and cell values match expectations before modifying the actual SQLite file.

### B. SQLite Specialists & Edge/Embedded Database Practitioners
- **Profile**: Engineers maintaining local-first desktop apps (Electron, Tauri), mobile apps, embedded devices, IoT nodes, and edge databases (Fly.io, Cloudflare D1, Turso/LibSQL staging).
- **Pain Point**: Remote devices and desktop clients run unattended SQLite instances. If an app update ships a bad SQLite migration, the user's database is corrupted on their machine, rendering the app unusable.
- **Value**: Pre-promotion verification. LiteMigrate ensures foreign keys, triggers, and page-level integrity hold true before promotion.

### C. Backend, DevOps & CI/CD Platform Engineers
- **Profile**: Platform teams managing automated deployment pipelines and testing workflows.
- **Pain Point**: Database migration failures in production halt deployments or force messy rollbacks. Traditional tests against empty test databases fail to reveal performance degradation or constraint violations on populated production schemas.
- **Value**: Deterministic CLI with explicit exit codes and structured JSON audit reports. Can run in CI against sanitized snapshot clones with sub-millisecond clone overhead.

---

## 2. The Core Problem: Why Successful SQL Execution Does Not Mean a Safe Migration

Most migration tools (Alembic, Flyway, Django migrations, Goose) answer a simple question:  
*"Did the database execute the SQL statements without throwing a syntax error?"*

In SQLite, this question is dangerously insufficient:
1. **Foreign Key Cascade Annihilation**: With `PRAGMA foreign_keys = ON;`, dropping a parent table or deleting parent rows can silently wipe hundreds of thousands of child rows across multiple tables with zero errors.
2. **Table Rebuild Inaccuracies**: Because SQLite has limited `ALTER TABLE` capabilities, developers rewrite tables using the 12-step rebuild procedure (`CREATE TABLE new... INSERT INTO new SELECT... DROP TABLE old... RENAME new TO old`). An omitted column or mismatched type in the `SELECT` query results in silent truncation or data loss.
3. **Implicit Type Conversions**: SQLite's dynamic type system will happily store text in integer columns unless `STRICT` mode is active, causing subtle data corruption during ETL migrations.
4. **Concurrent Clobbering (Lost Updates)**: Applying a long-running migration to a live SQLite file while another process writes can result in database lock timeouts or corrupted state.

---

## 3. The Solution: Shadow Verification

```
[ Active SQLite DB ] 
        │
        ▼ (Copy-on-write reflink or Online Backup API)
[ Isolated Shadow Database ]
        │
        ├─► 1. Pre-Migration Baseline (schema, row fingerprints, triggers)
        ├─► 2. Run Migration SQL
        ├─► 3. Multi-Invariant Audit (PRAGMA integrity_check, PRAGMA foreign_key_check)
        ├─► 4. Policy Check (block undeclared drops or row losses)
        │
        ▼
   [ Verdict ] ───► FAILED: Shadow discarded, Source untouched, Audit report generated.
        │
     PASSED
        │
        ▼ (Only on `litemigrate apply --confirm`)
[ Pre-Migration Backup (.bak) ] ──► [ CAS Concurrency Check ] ──► [ Apply to Source ]
```

---

## 4. Messaging Architecture

| Level | Message |
|:---|:---|
| **One-Sentence Pitch** | LiteMigrate is a local-first SQLite migration safety tool that validates migrations against an isolated shadow copy before promoting them to your database. |
| **Short Tagline** | *Test before you migrate. Validate first. Promote safely.* |
| **30-Second Elevator Pitch** | "In SQLite, a migration that executes without throwing a syntax error can still silently delete child rows via foreign key cascades or drop undeclared columns. LiteMigrate creates an isolated copy-on-write shadow clone of your SQLite database in less than a millisecond, executes your migration inside the sandbox, audits data preservation and integrity, and only touches your live database after all invariants pass." |

---

## 5. Key Technical Pillars

1. **Local-First & Zero-Cloud**: 100% offline. Zero telemetry, zero external cloud dependencies, zero database uploads. Your schemas and rows never leave your local machine.
2. **Sub-Millisecond Shadow Cloning**: Uses copy-on-write filesystem reflinks (APFS clonefile on macOS, FICLONE on Linux) or the SQLite Online Backup API. Creating an isolated sandbox takes < 1 ms on supported filesystems.
3. **Multi-Invariant Audit**:
   - Schema snapshot comparison (detects dropped tables, altered columns, lost indexes, missing triggers).
   - Streaming row fingerprinting (verifies existing data was not silently modified or lost).
   - Foreign key constraint validation (`PRAGMA foreign_key_check`).
   - SQLite page-level integrity (`PRAGMA integrity_check`).
4. **Concurrency-Safe Promotion (CAS)**: Before applying validated changes to the live database, LiteMigrate verifies `PRAGMA data_version` and schema cookies under an exclusive writer lock (`BEGIN IMMEDIATE`). If concurrent writes occurred, promotion immediately aborts without touching data.
5. **Conservative Policy Enforcement**: By default, no table drop, row truncation, or schema destruction is permitted. Destructive changes require an explicit, auditable `policy.json`.

---

## 6. Competitive Comparison Matrix

| Feature / Guarantee | Raw SQL / CLI (`sqlite3 db < mig.sql`) | Migration Frameworks (Alembic / Django) | Staging Environment Restore | **LiteMigrate** |
|:---|:---:|:---:|:---:|:---:|
| **Isolated Execution Before Live Write** | ❌ No | ❌ No | ⚠️ Partial (slow, complex) | ✅ **Yes (Isolated Shadow Copy)** |
| **Sub-Millisecond Sandbox Creation** | ❌ N/A | ❌ N/A | ❌ Minutes to hours | ✅ **< 1ms via CoW Reflinks** |
| **Foreign Key Constraint Verification** | ❌ Only if enabled | ❌ Only if enabled | ⚠️ Manual query | ✅ **Automated `foreign_key_check`** |
| **Physical Integrity Verification** | ❌ No | ❌ No | ⚠️ Manual query | ✅ **Automated `integrity_check`** |
| **Silent Row-Loss Detection** | ❌ No | ❌ No | ❌ No | ✅ **Automated Row Fingerprinting** |
| **Accidental Drop Prevention** | ❌ No | ⚠️ Requires code review | ❌ No | ✅ **Strict Policy Requirement** |
| **Concurrency Detection (CAS)** | ❌ Lock error or clobber | ❌ Lock error | ❌ N/A | ✅ **`data_version` CAS Check** |
| **Automated Pre-Promotion Backup** | ❌ Manual | ❌ Manual | ❌ N/A | ✅ **Automated Timestamped `.bak`** |
| **Cloud Independence & Privacy** | ✅ Local | ✅ Local | ⚠️ Often cloud-hosted | ✅ **100% Local-First** |

