# LiteMigrate — Phase 5 Security Review & Hardening Verification

**Date:** November 10, 2026  
**Scope:** Remediation of `S-01`, `S-02`, `S-03`, and `S-04` across `database_setup.py` and `prototype_shadow_migrate.py`

---

## 1. Threat Model & Attack Vectors Addressed

LiteMigrate operates on local developer machines and CI/CD runners where:
1. **Multi-user / shared runner filesystems** may expose world-readable temporary files (`umask 0o022`) containing sensitive production/staging database rows (`S-01`).
2. **Local symlink / path-prediction attacks** in shared directories could trick a privileged or automated migration runner into overwriting arbitrary target files via dangling symlinks (`S-02`).
3. **Untrusted or third-party SQLite database files** may embed malicious SQL functions, virtual tables, or triggers inside `sqlite_master` views/indexes/triggers that execute automatically during `PRAGMA integrity_check` or `SELECT` queries when `PRAGMA trusted_schema` is left at its SQLite compile-time default (`ON` / `1`) ([CVE-2020-13630](https://nvd.nist.gov/vuln/detail/CVE-2020-13630), [SQLite Defense Against The Dark Arts](https://www.sqlite.org/security.html)) (`S-03`, `S-04`).

---

## 2. Security Controls Implemented

### 2.1 Private `0o600` File Descriptor Creation & `0o700` Workspace Isolation (`S-01`)
- **Control:** `_open_secure_shadow_fd(shadow_path, source_mode)` creates every shadow database file using low-level POSIX `os.open()`:
  ```python
  flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
  fd = os.open(str(shadow_path), flags, 0o600)
  os.fchmod(fd, (source_mode & 0o777) & 0o600 or 0o600)
  ```
- **Directory Isolation:** When `shadow_path` is not explicitly provided, `execute_and_validate_shadow_migration()` creates a dedicated directory via `tempfile.mkdtemp(prefix=".litemigrate_shadow_", dir=str(source_path.parent))` and immediately enforces `os.chmod(temp_shadow_dir, 0o700)`.
- **Verification (`test_finding_s01`, `test_07_0600_source_database_produces_0600_shadow_across_all_strategies`):** Verified under an explicit `os.umask(0o022)` across both `CloneStrategy.LINUX_FICLONE` and `CloneStrategy.SQLITE_BACKUP_API` that `stat.S_IMODE(shadow_path.stat().st_mode) == 0o600` (`-rw-------`).

### 2.2 Symlink Rejection & `O_NOFOLLOW` Enforcement (`S-02`)
- **Control:**
  1. `_reject_symlink(path)` checks `path.is_symlink()` (`lstat` without following links) on `source_path`, `shadow_path`, `<source>-wal`, `<source>-shm`, `<source>-journal`, and `<source>.litemigrate.lock` before opening any descriptor.
  2. Because `Path.exists()` returns `False` for a **dangling symlink** while `Path.is_symlink()` returns `True`, checking `is_symlink()` before `exists()` catches dangling symlinks deterministically.
  3. Opening `shadow_path` with `os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW` provides kernel-enforced atomic rejection if a symlink or file is raced into place.
- **Verification (`test_finding_s02`, `test_08_dangling_symlink_at_temporary_destination_rejected`):** Verified that pointing a dangling symlink at `nonexistent_victim.txt` raises `PermissionError("Security Error: Refusing to operate on symlinked path ...")` and never creates `nonexistent_victim.txt`.

### 2.3 Mandatory `PRAGMA trusted_schema = OFF` Enforcement & Read-Back Verification (`S-03`)
- **Control:** Both `database_setup._enforce_untrusted_schema(conn)` and `prototype_shadow_migrate._enforce_untrusted_schema(conn)` execute:
  ```python
  conn.execute("PRAGMA trusted_schema = OFF;")
  val = conn.execute("PRAGMA trusted_schema;").fetchone()
  if val is None or int(val[0]) != 0:
      raise RuntimeError(f"Security Error: Failed to enforce PRAGMA trusted_schema = OFF (got {val!r}).")
  ```
- **Coverage:** Enforced on every connection created in `connect_sqlite()`, `_open_Hardened_connection()`, `create_shadow_database()`, `compute_logical_db_digest()`, `execute_and_validate_shadow_migration()`, and `_promote_shadow_to_source()`.
- **Verification (`test_finding_s03`, `test_09_trusted_schema_read_back_on_every_connection`):** Verified that `PRAGMA trusted_schema;` returns `0` inside both helper connections and user-supplied migration callables, and that a Python UDF marked as non-innocuous/direct-only placed inside a `VIEW` or `CHECK` constraint is blocked by SQLite when queried under `trusted_schema = OFF`.

### 2.4 Safe Execution Order of `PRAGMA foreign_key_check` & `PRAGMA integrity_check` (`S-04`)
- **Control:** During Stage 5 post-migration auditing on `shadow_conn`:
  1. `_enforce_untrusted_schema(shadow_conn)` is re-verified immediately after the migration script finishes (preventing a migration script that attempted `PRAGMA trusted_schema = ON;` from leaving the connection in a trusted state during the audit!).
  2. `PRAGMA foreign_key_check;` is executed first to catch referential integrity violations cleanly (`ValidationVerdict.BLOCKED_FOREIGN_KEY_VIOLATION`).
  3. `PRAGMA integrity_check;` / `PRAGMA quick_check;` is executed only while `trusted_schema == 0` is confirmed active.
