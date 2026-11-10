# LiteMigrate Alpha Test Plan (v0.1.0-alpha.1)

This document specifies the operational test plan, verification methodology, and empirical test matrix executed for **LiteMigrate Alpha (`v0.1.0-alpha.1`)**.

---

## 1. Objectives & Scope

The Alpha testing plan validates:
1. **Safety Invariants**: That shadow validation accurately isolates migrations and catches integrity or constraint failures without altering the source database.
2. **SQLite Edge Cases**: That schema inspection, row hashing, and fingerprinting operate reliably across SQLite's various storage modes (`WITHOUT ROWID`, `STRICT`, column aliases, WAL mode, composite keys).
3. **Failure Resilience**: That destructive mutations without explicit permission, corrupted databases, and concurrent source writes cleanly abort promotion and protect data.
4. **Usability & Determinism**: That CLI exits codes, audit logs, and JSON serialization are predictable and reproducible.

---

## 2. 18-Scenario Operational Test Matrix

The following 18 scenarios are implemented as automated regression tests in [`tests/alpha_matrix/test_alpha_matrix.py`](../tests/alpha_matrix/test_alpha_matrix.py) and executed against Python 3.10, 3.11, 3.12, and 3.13 on macOS, Linux, and Windows.

| # | Scenario Description | Test Methodology | Pass Criteria | Empirical Result |
|:---|:---|:---|:---|:---|
| **1** | **Standard Rowid Tables** (Single & Composite PK) | Create single-column and composite PK tables with data; alter columns and add indexes. | Schema diff detected; row fingerprints preserved; verdict PASS. | **PASS** |
| **2** | **WITHOUT ROWID Tables** | Create table with `WITHOUT ROWID` and multi-column primary key; migrate and verify. | Correct column extraction without referencing hidden `rowid`; fingerprint matches; verdict PASS. | **PASS** |
| **3** | **Explicit `rowid`, `_rowid_`, `oid` Columns** | Create tables with explicit user columns named `rowid`, `_rowid_`, or `oid`. | No collision between SQLite hidden rowid and explicit user columns; exact value hashing preserved. | **PASS** |
| **4** | **SQLite `STRICT` Mode Tables** | Create table with `STRICT` table option (`id INT, val TEXT) STRICT;`. Validate type constraint enforcement during migration. | Schema parsed without error; invalid type insertions during migration fail safety checks. | **PASS** |
| **5** | **WAL Mode Under Active Connection** | Enable `PRAGMA journal_mode=WAL;` with active uncheckpointed write connections during shadow clone. | `sqlite3_backup_*` creates consistent page clone without blocking reader/writer; verdict PASS. | **PASS** |
| **6** | **Foreign Key Violations** | Enable `PRAGMA foreign_keys=ON;`. Attempt migration that inserts orphaned child records or drops parent records. | `PRAGMA foreign_key_check` detects violation; migration rejected with `FOREIGN_KEY_VIOLATION`. | **PASS** |
| **7** | **View & Trigger Modifications** | Create dependent views and triggers; alter base tables and verify trigger persistence or schema changes. | Schema diff correctly reports view/trigger additions, modifications, or removals. | **PASS** |
| **8** | **Non-ASCII Identifiers (UTF-8)** | Create tables and columns with international UTF-8 names (e.g., `données`, `ユーザー`, `каталог`). | SQLite and LiteMigrate quoting handles unicode identifiers without parser error or hashing mismatch. | **PASS** |
| **9** | **Extreme SQLite Values** | Populate tables with `NULL`, raw binary `BLOB` (including null bytes), empty strings, and IEEE-754 `-0.0`. | Fingerprinting correctly differentiates `0.0` from `-0.0` and preserves distinct null/blob hashes. | **PASS** |
| **10** | **Destructive Operation Rejection** | Attempt `DROP TABLE` or `DELETE FROM table;` under default policy (`allow_destructive=False`). | Migration rejected with `DESTRUCTIVE_CHANGE_REJECTED`; source database untouched. | **PASS** |
| **11** | **Destructive Operation Allowance** | Execute table drop or column deletion with `--allow-destructive` / `allow_destructive=True`. | Destructive policy warning logged; migration passes validation and successfully promotes. | **PASS** |
| **12** | **Pre-Migration Backup & Rollback** | Apply a migration to live database with confirmation. Verify pre-migration `.bak` file existence and fidelity. | Pre-migration `.bak` created before live write; verified byte-level or logical content parity. | **PASS** |
| **13** | **Concurrency-Abort (CAS Check)** | Modify source database concurrently after shadow validation but before promotion. | Promotion detects `PRAGMA data_version` / schema cookie change; aborts with `SOURCE_MODIFIED_CONCURRENTLY`. | **PASS** |
| **14** | **Corrupted Database Handling** | Introduce simulated corruption into database file headers/pages. Run validation. | `PRAGMA integrity_check` reports errors; validation aborts safely with integrity failure. | **PASS** |
| **15** | **Multi-Statement & Transactions** | Execute complex multi-statement SQL with explicit `BEGIN` / `COMMIT` blocks and DDL/DML mixes. | Entire transaction sequence executes cleanly on shadow; state verified atomically. | **PASS** |
| **16** | **Callable Migration Rejection** | Submit Python callable or function as migration payload to API and promotion boundaries. | Engine rejects callable at entry; refuses to promote non-SQL migration scripts. | **PASS** |
| **17** | **Performance & Memory Scaling** | Clone and fingerprint table with 10,000+ rows and multiple indexes. Benchmark duration. | Shadow copy completes in < 50ms; fingerprinting executes in streaming batches without high memory usage. | **PASS** |
| **18** | **Report JSON Serialization** | Run migration and export `AuditReport` to JSON (`to_dict()` / `to_json()`). | All dataclass fields (enums, Path objects, diffs) serialize cleanly without TypeError. | **PASS** |

---

## 3. Pass/Fail Criteria

A test scenario passes if and only if:
1. **Safety Decision Integrity**: Destructive or invalid migrations are never permitted under default settings.
2. **Zero Involuntary Source Mutation**: When validation fails or aborts, the source database remains byte-for-byte or logically identical to its initial state.
3. **Process Determinism**: CLI commands return predictable exit codes (`0` for success, `1` for execution error, `2` for validation rejection).
4. **Typed Contract Compliance**: No unhandled exceptions, type errors, or serialization crashes occur.

---

## 4. Empirical Test Verification Command

Testers and developers can run the entire test suite including the Alpha Matrix locally:

```bash
# Run unit tests and alpha matrix suite
pytest tests/
# Or via standard library unittest
python3 -m unittest discover -v -s tests -t . -p "test_*.py"

# Type checking and linting
mypy src tests/alpha_matrix
ruff check src tests
```
