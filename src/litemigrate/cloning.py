"""Shadow database creation via copy-on-write (APFS/FICLONE) and bounded backup API."""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
import tempfile
import time
from pathlib import Path

from litemigrate.models import CloneStrategy, ShadowCloneResult
from litemigrate.sqlite_backend import bounded_sqlite_backup, open_hardened_sqlite

# Linux ioctl constant for copy-on-write reflink cloning (<linux/fs.h>)
LINUX_FICLONE = 0x40049409


def reject_symlink(path: Path) -> None:
    """Ensure path is not a symlink, preventing arbitrary file overwrite vulnerabilities."""
    if path.is_symlink():
        raise PermissionError(
            f"Security violation: Symlinks are forbidden for database paths: {path}"
        )


def ensure_safe_destination_path(dst: Path) -> None:
    """Validate that destination path does not collide with existing or symlinked files."""
    reject_symlink(dst)
    if dst.exists():
        dst.unlink()
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(f"{dst}{suffix}")
        if sidecar.is_symlink():
            raise PermissionError(
                f"Security violation: Refusing to use symlinked sidecar path: {sidecar}"
            )
        if sidecar.exists():
            sidecar.unlink()


def try_apfs_clonefile(src: Path, dst: Path) -> None:
    """Invoke macOS Darwin clonefile(2) via libc and enforce 0o600 permissions."""
    if sys.platform != "darwin":
        raise OSError("clonefile(2) is only available on macOS / Darwin systems.")

    ensure_safe_destination_path(dst)

    libc_path = ctypes.util.find_library("c")
    if not libc_path:
        raise OSError("Unable to locate Darwin libc for clonefile(2).")

    libc = ctypes.CDLL(libc_path, use_errno=True)
    clonefile_fn = getattr(libc, "clonefile", None)
    if clonefile_fn is None:
        raise OSError("Symbol clonefile not found in Darwin libc.")

    clonefile_fn.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32]
    clonefile_fn.restype = ctypes.c_int

    # CLONE_NOFOLLOW = 0x0001
    res = clonefile_fn(os.fsencode(src), os.fsencode(dst), ctypes.c_uint32(0x0001))
    if res != 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err), str(src), None, str(dst))

    os.chmod(dst, 0o600)


def try_linux_ficlone(src: Path, dst: Path) -> None:
    """Invoke Linux ioctl(dst_fd, FICLONE, src_fd) into an O_EXCL | O_NOFOLLOW 0o600 file."""
    if not sys.platform.startswith("linux"):
        raise OSError("FICLONE ioctl is only available on Linux.")

    ensure_safe_destination_path(dst)

    open_flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    dst_fd = os.open(str(dst), open_flags, 0o600)
    try:
        os.fchmod(dst_fd, 0o600)
        with open(src, "rb") as f_src:
            import fcntl
            fcntl.ioctl(dst_fd, LINUX_FICLONE, f_src.fileno())
    except OSError:
        try:
            os.unlink(dst)
        except OSError:
            pass
        raise
    else:
        os.close(dst_fd)


def create_shadow_database(
    source_db: Path | str,
    shadow_db: Path | str | None = None,
    *,
    strategy: CloneStrategy = CloneStrategy.AUTO,
    busy_timeout_ms: int = 3000,
    temp_dir: Path | None = None,
) -> ShadowCloneResult:
    """Create a private, transactionally consistent shadow copy of `source_db`."""
    raw_source = Path(source_db)
    reject_symlink(raw_source)
    source_path = raw_source.resolve()

    if not source_path.exists():
        raise FileNotFoundError(f"Source database not found: {source_path}")

    # Determine shadow destination path
    if shadow_db is None:
        if temp_dir is None:
            workspace = Path(tempfile.mkdtemp(prefix="litemigrate_"))
            os.chmod(workspace, 0o700)
        else:
            workspace = Path(temp_dir)
        shadow_path = workspace / f"{source_path.stem}.shadow.db"
    else:
        raw_shadow = Path(shadow_db)
        reject_symlink(raw_shadow)
        shadow_path = raw_shadow.resolve()

    ensure_safe_destination_path(shadow_path)

    # Check WAL sidecar activity
    wal_path = Path(f"{source_path}-wal")
    has_active_sidecar = False
    wal_size = 0
    if wal_path.is_symlink():
        raise PermissionError(f"Security violation: Symlinked WAL file detected: {wal_path}")
    if wal_path.exists():
        wal_size = wal_path.stat().st_size
        if wal_size > 0:
            has_active_sidecar = True

    try:
        src_conn = open_hardened_sqlite(source_path, busy_timeout_ms=busy_timeout_ms, read_only=True)
        try:
            cur = src_conn.execute("PRAGMA journal_mode;")
            jmode = (cur.fetchone() or [""])[0].lower()
            if jmode == "wal":
                has_active_sidecar = True
        finally:
            src_conn.close()
    except Exception:
        pass

    t0 = time.perf_counter()
    notes: list[str] = []

    # If active WAL frames exist, raw file cloning is unsafe because it misses uncheckpointed WAL frames.
    # We must use the bounded SQLite backup API.
    if has_active_sidecar:
        bounded_sqlite_backup(source_path, shadow_path, busy_timeout_ms=busy_timeout_ms)
        notes.append(
            f"Active WAL frames detected ({wal_size} bytes); used transactionally consistent "
            "bounded SQLite Backup API."
        )
        return ShadowCloneResult(
            shadow_path=shadow_path,
            strategy_used=CloneStrategy.SQLITE_BACKUP_API,
            duration_ms=(time.perf_counter() - t0) * 1000.0,
            wal_required_backup_fallback=True,
            wal_size_bytes_at_clone=wal_size,
            notes=tuple(notes),
        )

    # Attempt copy-on-write clone if requested or AUTO
    if strategy in (CloneStrategy.AUTO, CloneStrategy.APFS_CLONEFILE) and sys.platform == "darwin":
        try:
            try_apfs_clonefile(source_path, shadow_path)
            notes.append("Created shadow database via macOS APFS clonefile(2).")
            return ShadowCloneResult(
                shadow_path=shadow_path,
                strategy_used=CloneStrategy.APFS_CLONEFILE,
                duration_ms=(time.perf_counter() - t0) * 1000.0,
                wal_required_backup_fallback=False,
                wal_size_bytes_at_clone=0,
                notes=tuple(notes),
            )
        except OSError as exc:
            if strategy == CloneStrategy.APFS_CLONEFILE:
                raise
            notes.append(f"APFS clonefile(2) unavailable ({exc}); falling back to bounded SQLite Backup API.")

    if strategy in (CloneStrategy.AUTO, CloneStrategy.LINUX_FICLONE) and sys.platform.startswith("linux"):
        try:
            try_linux_ficlone(source_path, shadow_path)
            notes.append("Created shadow database via Linux FICLONE ioctl.")
            return ShadowCloneResult(
                shadow_path=shadow_path,
                strategy_used=CloneStrategy.LINUX_FICLONE,
                duration_ms=(time.perf_counter() - t0) * 1000.0,
                wal_required_backup_fallback=False,
                wal_size_bytes_at_clone=0,
                notes=tuple(notes),
            )
        except OSError as exc:
            if strategy == CloneStrategy.LINUX_FICLONE:
                raise
            notes.append(f"Linux FICLONE unavailable ({exc}); falling back to bounded SQLite Backup API.")

    # Universal fallback
    bounded_sqlite_backup(source_path, shadow_path, busy_timeout_ms=busy_timeout_ms)
    notes.append("Created shadow database via bounded libsqlite3 Backup API.")
    return ShadowCloneResult(
        shadow_path=shadow_path,
        strategy_used=CloneStrategy.SQLITE_BACKUP_API,
        duration_ms=(time.perf_counter() - t0) * 1000.0,
        wal_required_backup_fallback=False,
        wal_size_bytes_at_clone=0,
        notes=tuple(notes),
    )
