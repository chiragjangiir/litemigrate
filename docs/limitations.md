# LiteMigrate — Platform Boundaries & Known Limitations

LiteMigrate is honest about its operating assumptions and what it cannot prove.

## Supported vs. Unsupported Migration Interfaces

### Supported
- **SQL Migration Scripts:** String or file-based standard SQL DDL and DML statements. Executed inside an atomic `BEGIN IMMEDIATE ... COMMIT` block.

### Explicitly Excluded
- **Arbitrary Python Callables:** `Callable[[sqlite3.Connection], None]` migrations are rejected in the public API. Arbitrary callables cannot be guaranteed atomic under SQLite transaction boundaries, may execute uncontrolled side effects, and risk partial source modification.

## Storage Engines & Databases

LiteMigrate v0.1.0-alpha.1 strictly targets **SQLite**.
- **DuckDB:** Out of scope for this milestone.
- **LibSQL / Turso:** Out of scope for this milestone.
- **Client-Server RDBMS (PostgreSQL, MySQL):** Not supported.

## Platform Clone Strategies

| Platform | Filesystem | Clone Mechanism | Status |
| :--- | :--- | :--- | :--- |
| **macOS (Darwin)** | Apple APFS | `clonefile(2)` via Darwin libc | **Verified on native Apple Silicon APFS** |
| **Linux** | XFS / Btrfs | `ioctl(..., FICLONE)` | **Verified on Linux 6.x XFS** |
| **Universal POSIX** | Any POSIX filesystem | `sqlite3_backup_*` C API | **Verified universal fallback** |

## Threat & Concurrency Boundaries

1. **Non-SQLite File Tampering:** LiteMigrate assumes all database interactions comply with SQLite's locking protocol. Direct manipulation of database file bytes via raw filesystem APIs cannot be prevented.
2. **Optimistic Validation Window:** LiteMigrate does not block production writers while shadow validation is running (which could take several seconds on large databases). If a writer commits during validation, promotion cleanly aborts.
3. **Local Storage Only:** In-memory databases (`:memory:`) and remote network mounts lacking POSIX advisory lock support (NFS/SMB without locking) are not supported.
