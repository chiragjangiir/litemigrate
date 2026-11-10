# LiteMigrate — Launch Response Playbook

This document prepares the core engineering and maintainer team for community interactions during the launch on Hacker News (Show HN), Reddit (r/Python), and developer forums.

---

## 1. Core Principles of Community Engagement

1. **Never Argue Defensively**: Welcome skepticism and tough technical questions. If someone points out a flaw or edge case, thank them and investigate.
2. **Be Transparent About Limits**: Freely acknowledge what LiteMigrate does *not* do. Never pretend the tool solves every database challenge.
3. **Separate Bugs from Expected Invariant Enforcements**: If a user is surprised that an undeclared table drop failed, explain that LiteMigrate is intentionally conservative by default.
4. **Demand Minimal Reproductions, Not Real Data**: Always protect user privacy. Never ask a commenter to upload their proprietary database file.

---

## 2. Common Technical Questions & Prepared Responses

### Q1: "Doesn't SQLite already support transactions for migrations? Why do I need a shadow copy?"
> **Response**:  
> "SQLite does support transactions for many DDL operations, but there are two key gaps:  
> 1. In SQLite, many schema changes require the 12-step table rebuild procedure (creating a temporary table, copying rows via `INSERT INTO ... SELECT`, dropping the original table, and renaming). If you omit a column or make a type mistake in that SELECT statement, the transaction commits cleanly with exit code 0—while permanently dropping data.  
> 2. With foreign keys enabled, `ON DELETE CASCADE` can silently wipe related child tables during table rebuilds or cleanup queries without raising an error.  
> 
> LiteMigrate verifies that existing data survived, foreign keys hold (`PRAGMA foreign_key_check`), and page integrity passes *before* any change reaches your source database."

---

### Q2: "How is this different from Alembic or Django migrations?"
> **Response**:  
> "LiteMigrate is an execution safety harness, not an ORM or a migration generator. Tools like Alembic and Django generate SQL and verify that the database executed the statements without throwing syntax errors. LiteMigrate validates that data and relational invariants survived the migration. You can use LiteMigrate alongside Alembic or plain SQL scripts to ensure safety."

---

### Q3: "Isn't copying a large database too slow for production deployments?"
> **Response**:  
> "On modern filesystems (macOS APFS and Linux Btrfs/XFS), LiteMigrate uses kernel copy-on-write reflinks (`clonefile` on macOS, `ioctl(FICLONE)` on Linux). Instead of copying data blocks, the filesystem creates a lightweight pointer to existing physical extents. Creating a shadow clone of a 10 GB database takes under 1 millisecond and allocates zero extra disk space until pages are modified.  
> 
> On filesystems without reflink support, or when uncheckpointed WAL frames are active, LiteMigrate falls back to the SQLite Online Backup API, which copies pages sequentially without blocking readers or writers."

---

### Q4: "How does LiteMigrate handle concurrency if another process writes during validation?"
> **Response**:  
> "Before applying a migration (`litemigrate apply --confirm`), LiteMigrate acquires an exclusive writer lock (`BEGIN IMMEDIATE`) on the source database. Under this lock, it re-reads `PRAGMA data_version` and the schema cookie. If another process committed data while validation was running, LiteMigrate's Compare-And-Swap (CAS) check detects the change and immediately aborts promotion without touching the source database."

---

### Q5: "Why do you reject Python callable migrations? Alembic uses Python functions."
> **Response**:  
> "We intentionally restricted `v0.1.0-alpha.1` to SQL-only migrations. Arbitrary Python callables can execute non-deterministic side effects (making network calls, reading environment variables, or mutating external files) that cannot be safely rolled back or audited across isolated shadow processes. We may evaluate isolated worker sandboxes in future Beta releases, but for Alpha, SQL-only guarantees deterministic verification."

---

### Q6: "Why isn't this published on PyPI?"
> **Response**:  
> "LiteMigrate is currently an experimental Alpha (`v0.1.0-alpha.1`). Because this is a database safety tool, we want independent verification of our concurrency locking and row hashing invariants before encouraging automated `pip install litemigrate` in production CI pipelines. Testers can install the verified wheel directly from our GitHub Releases page."

---

## 3. Handling Criticism & Skepticism

| Critic Comment | Recommended Demeanor & Response |
|:---|:---|
| *"This is totally unnecessary. I just test my migrations in staging."* | "That's a solid workflow if you have a staging environment that perfectly mirrors production data volumes. LiteMigrate is designed for local-first apps, desktop apps, and CI environments where running a full staging replica is too heavy or slow." |
| *"SQLite is an embedded database, nobody needs this level of complexity."* | "Many modern architectures (like Fly.io, Turso, Cloudflare D1, and local-first Tauri/Electron apps) run critical production workloads on SQLite. When you can't easily SSH into thousands of distributed client databases to fix a broken migration, pre-promotion verification is a lifesaver." |
| *"Your tool rejected my migration even though it works fine in sqlite3 CLI!"* | "LiteMigrate is strictly conservative by default: it blocks table drops and row deletions unless declared in an explicit `policy.json`. If this was an intentional drop, you can allow it via `--policy policy.json`. If not, LiteMigrate may have caught an unintentional side-effect!" |

---

## 4. How to Handle Bug Reports & Feature Requests

### When Someone Reports a Bug:
1. Thank them immediately for testing the Alpha.
2. Ask for their OS, Python version, and SQLite version (`python3 -c "import platform, sqlite3; print(platform.platform(), sqlite3.sqlite_version)"`).
3. Request a **synthetic minimal reproduction SQL script** (remind them never to attach their real database).
4. Direct them to our structured [Bug Report Template](https://github.com/chiragjangiir/litemigrate/issues/new?template=alpha_bug_report.md).

### When Someone Requests a Feature:
1. Acknowledge the use case and check if it is already covered in [`ROADMAP.md`](../ROADMAP.md).
2. Point them to the roadmap and invite them to contribute to the discussion on GitHub Issues.
