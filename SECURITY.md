# Security Policy

LiteMigrate treats database security, privacy, and integrity as foundational requirements.

## Supported Versions

| Version | Supported |
| :--- | :--- |
| `0.1.x` (Alpha) | Yes |

---

## Security Guarantees & Threat Model

LiteMigrate enforces several defense-in-depth security controls:
1. **Untrusted Schema Defense:** Enforces `PRAGMA trusted_schema = OFF;` on all connections to prevent malicious virtual-table or UDF execution embedded in SQLite schemas ([CVE-2020-13630](https://nvd.nist.gov/vuln/detail/CVE-2020-13630)).
2. **Symlink Traversal Prevention:** Disallows symlinks on source database paths, shadow database destinations, sidecars (`-wal`, `-shm`, `-journal`), and lock files.
3. **Restricted File Modes:** All created shadow copies, rollback backups, and advisory locks are created with explicit `0o600` (`-rw-------`) permissions under `0o700` isolated directories.
4. **Local Execution Only:** Zero network calls, zero telemetry, and zero transmission of database schemas or contents.

### Explicit Non-Guarantees (Out-of-Scope)
- **Local Host Attackers with Raw Filesystem Access:** If an unprivileged user has raw write access to the database file on disk and bypasses SQLite locking, SQLite cannot prevent file tampering.
- **Physical Memory Extraction:** Database contents reside unencrypted in local system memory while being fingerprinted.

---

## Reporting a Vulnerability

If you discover a security vulnerability in LiteMigrate:
1. **Do not open a public GitHub issue.**
2. Send a confidential report to `184008125+chiragjangiir@users.noreply.github.com`.
3. Provide a reproduction script or minimal adversarial test demonstrating the issue.
4. We will acknowledge receipt within 48 hours and work with you on a coordinated disclosure timeline.
