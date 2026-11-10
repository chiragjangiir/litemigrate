"""Hardened SQLite connection utilities, native libsqlite3 C bindings, and lexer tools."""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import sqlite3
import time
from pathlib import Path
from typing import Literal

# SQLite C API return codes and flags
SQLITE_OK = 0
SQLITE_BUSY = 5
SQLITE_LOCKED = 6
SQLITE_DONE = 101
SQLITE_OPEN_READONLY = 0x00000001
SQLITE_OPEN_READWRITE = 0x00000002
SQLITE_OPEN_CREATE = 0x00000004
SQLITE_OPEN_NOMUTEX = 0x00008000

_LIBSQLITE: ctypes.CDLL | None = None


def escape_identifier(name: str) -> str:
    """Safely escape a SQLite identifier using double quotes."""
    escaped = name.replace('"', '""')
    return f'"{escaped}"'


def enforce_untrusted_schema(conn: sqlite3.Connection) -> None:
    """Enforce and verify PRAGMA trusted_schema = OFF on every connection.

    Protects against schema-embedded malicious functions or triggers executing during
    PRAGMA integrity_check, foreign_key_check, or schema introspection (CVE-2020-13630).
    """
    conn.execute("PRAGMA trusted_schema = OFF;")
    val = conn.execute("PRAGMA trusted_schema;").fetchone()
    if not val or val[0] != 0:
        raise RuntimeError(
            "Security violation: PRAGMA trusted_schema could not be set to OFF (read back non-zero)."
        )


def open_hardened_sqlite(
    db_path: Path | str,
    *,
    busy_timeout_ms: int = 3000,
    read_only: bool = False,
    isolation_level: Literal["DEFERRED", "EXCLUSIVE", "IMMEDIATE"] | None = None,
) -> sqlite3.Connection:
    """Open a SQLite connection with hardened security settings and timeout enforcement."""
    p = Path(db_path)
    if p.is_symlink():
        raise PermissionError(
            f"Security violation: Refusing to open symlinked SQLite database: {p}"
        )

    if read_only:
        uri = f"file:{p.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=busy_timeout_ms / 1000.0, isolation_level=isolation_level)
    else:
        conn = sqlite3.connect(str(p), timeout=busy_timeout_ms / 1000.0, isolation_level=isolation_level)

    enforce_untrusted_schema(conn)
    conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)};")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_libsqlite() -> ctypes.CDLL:
    """Locate and return the loaded libsqlite3 shared library with typed C signatures."""
    global _LIBSQLITE
    if _LIBSQLITE is None:
        lib_path = ctypes.util.find_library("sqlite3")
        if not lib_path:
            raise RuntimeError("Unable to locate libsqlite3 shared library on this system.")
        lib = ctypes.CDLL(lib_path)

        lib.sqlite3_open_v2.argtypes = [
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_int,
            ctypes.c_char_p,
        ]
        lib.sqlite3_open_v2.restype = ctypes.c_int

        lib.sqlite3_close_v2.argtypes = [ctypes.c_void_p]
        lib.sqlite3_close_v2.restype = ctypes.c_int

        lib.sqlite3_backup_init.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.c_char_p,
        ]
        lib.sqlite3_backup_init.restype = ctypes.c_void_p

        lib.sqlite3_backup_step.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.sqlite3_backup_step.restype = ctypes.c_int

        lib.sqlite3_backup_remaining.argtypes = [ctypes.c_void_p]
        lib.sqlite3_backup_remaining.restype = ctypes.c_int

        lib.sqlite3_backup_pagecount.argtypes = [ctypes.c_void_p]
        lib.sqlite3_backup_pagecount.restype = ctypes.c_int

        lib.sqlite3_backup_finish.argtypes = [ctypes.c_void_p]
        lib.sqlite3_backup_finish.restype = ctypes.c_int

        lib.sqlite3_errmsg.argtypes = [ctypes.c_void_p]
        lib.sqlite3_errmsg.restype = ctypes.c_char_p

        _LIBSQLITE = lib
    return _LIBSQLITE


def bounded_sqlite_backup(
    src_path: Path,
    dst_path: Path,
    *,
    busy_timeout_ms: int = 3000,
    pages_per_step: int = 128,
) -> None:
    """Copy `src_path` to `dst_path` using libsqlite3 C Backup API with a strict wall-clock deadline.

    Bypasses CPython's built-in `Connection.backup()` loop which sleeps indefinitely
    on SQLITE_BUSY ignoring PRAGMA busy_timeout. Opens connection handles directly
    via file paths using libsqlite3.
    """
    if dst_path.is_symlink():
        raise PermissionError(
            f"Security violation: Refusing to backup into symlink: {dst_path}"
        )

    if not dst_path.exists():
        open_flags = os.O_CREAT | os.O_EXCL | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(str(dst_path), open_flags, 0o600)
        os.fchmod(fd, 0o600)
        os.close(fd)
    else:
        os.chmod(dst_path, 0o600)

    lib = get_libsqlite()
    p_src = ctypes.c_void_p()
    p_dst = ctypes.c_void_p()
    deadline = time.monotonic() + max(0.02, busy_timeout_ms / 1000.0)

    rc_src = lib.sqlite3_open_v2(
        os.fsencode(src_path),
        ctypes.byref(p_src),
        SQLITE_OPEN_READONLY | SQLITE_OPEN_NOMUTEX,
        None,
    )
    if rc_src != SQLITE_OK:
        msg = (
            lib.sqlite3_errmsg(p_src).decode("utf-8", "replace")
            if p_src
            else f"sqlite error code {rc_src}"
        )
        if p_src:
            lib.sqlite3_close_v2(p_src)
        raise sqlite3.OperationalError(
            f"Failed to open source database for bounded backup ({src_path}): {msg}"
        )

    rc_dst = lib.sqlite3_open_v2(
        os.fsencode(dst_path),
        ctypes.byref(p_dst),
        SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_NOMUTEX,
        None,
    )
    if rc_dst != SQLITE_OK:
        msg = (
            lib.sqlite3_errmsg(p_dst).decode("utf-8", "replace")
            if p_dst
            else f"sqlite error code {rc_dst}"
        )
        lib.sqlite3_close_v2(p_src)
        if p_dst:
            lib.sqlite3_close_v2(p_dst)
        raise sqlite3.OperationalError(
            f"Failed to open destination database for bounded backup ({dst_path}): {msg}"
        )

    p_backup = ctypes.c_void_p()
    try:
        p_backup = lib.sqlite3_backup_init(
            p_dst,
            b"main",
            p_src,
            b"main",
        )
        if not p_backup:
            msg = lib.sqlite3_errmsg(p_dst).decode("utf-8", "replace")
            raise sqlite3.OperationalError(f"sqlite3_backup_init failed: {msg}")

        while True:
            rc_step = lib.sqlite3_backup_step(p_backup, int(pages_per_step))
            if rc_step == SQLITE_DONE:
                break
            if rc_step == SQLITE_OK:
                if time.monotonic() >= deadline:
                    raise sqlite3.OperationalError(
                        "database is locked (bounded backup timeout exceeded while stepping)"
                    )
                continue
            if rc_step in (SQLITE_BUSY, SQLITE_LOCKED):
                if time.monotonic() >= deadline:
                    raise sqlite3.OperationalError(
                        "database is locked (bounded backup timeout exceeded on lock contention)"
                    )
                time.sleep(0.01)
                continue

            msg = lib.sqlite3_errmsg(p_dst).decode("utf-8", "replace")
            raise sqlite3.OperationalError(
                f"sqlite3_backup_step failed with return code {rc_step}: {msg}"
            )
    finally:
        if p_backup:
            lib.sqlite3_backup_finish(p_backup)
        lib.sqlite3_close_v2(p_src)
        lib.sqlite3_close_v2(p_dst)


def split_sql_statements(sql_script: str) -> list[str]:
    """Split a SQL script into individual executable statements using SQLite's C lexer."""
    statements: list[str] = []
    buffer: list[str] = []

    for ch in sql_script:
        buffer.append(ch)
        if ch == ";":
            candidate = "".join(buffer)
            if sqlite3.complete_statement(candidate):
                stmt = _strip_leading_sql_comments(candidate)
                if stmt:
                    statements.append(stmt)
                buffer.clear()

    if buffer:
        remainder = _strip_leading_sql_comments("".join(buffer))
        if remainder:
            statements.append(remainder)
    return statements


def _strip_leading_sql_comments(sql: str) -> str:
    """Remove leading blank lines and `--` comment lines from a SQL statement chunk."""
    lines = sql.splitlines(keepends=True)
    idx = 0
    while idx < len(lines):
        s = lines[idx].strip()
        if not s or s.startswith("--"):
            idx += 1
        else:
            break
    return "".join(lines[idx:]).strip()


def cleanup_db_artifacts(path: Path) -> None:
    """Clean up ephemeral -wal, -shm, and -journal files associated with a database."""
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(f"{path}{suffix}")
        if sidecar.is_symlink() or sidecar.exists():
            try:
                sidecar.unlink()
            except OSError:
                pass
