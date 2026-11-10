"""Canonical cell encoding, row-identity resolution, and streaming table/column fingerprinting."""

from __future__ import annotations

import hashlib
import sqlite3
import struct
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from litemigrate.exceptions import UnsupportedTableStructureError
from litemigrate.sqlite_backend import escape_identifier, open_hardened_sqlite


def canonical_cell_bytes(val: Any) -> bytes:
    """Serialize a SQLite value into an unambiguous, type-prefixed byte string.

    Format:
      Null:    N:0:;
      Integer: I:<len>:<base10_digits>;
      Real:    R:8:<ieee754_bigendian_hex>;
      Text:    T:<byte_len>:<utf8_bytes>;
      Blob:    B:<byte_len>:<raw_bytes>;
    """
    if val is None:
        return b"N:0:;"
    if isinstance(val, bool):
        int_val = 1 if val else 0
        raw = str(int_val).encode("ascii")
        return f"I:{len(raw)}:".encode("ascii") + raw + b";"
    if isinstance(val, int):
        raw = str(val).encode("ascii")
        return f"I:{len(raw)}:".encode("ascii") + raw + b";"
    if isinstance(val, float):
        # Distinguish -0.0 from +0.0, NaN, and Infs using IEEE 754 64-bit big-endian representation
        packed = struct.pack(">d", val).hex().encode("ascii")
        return b"R:8:" + packed + b";"
    if isinstance(val, str):
        raw = val.encode("utf-8")
        return f"T:{len(raw)}:".encode("ascii") + raw + b";"
    if isinstance(val, (bytes, bytearray, memoryview)):
        raw_b = bytes(val)
        return f"B:{len(raw_b)}:".encode("ascii") + raw_b + b";"
    fallback = repr(val).encode("utf-8")
    return f"O:{len(fallback)}:".encode("ascii") + fallback + b";"


def get_table_identity_info(
    conn: sqlite3.Connection, table_name: str
) -> tuple[bool, tuple[str, ...]]:
    """Determine whether table has accessible physical `rowid` or requires primary key columns.

    Handles edge cases where user-defined columns shadow 'rowid', '_rowid_', and/or 'oid',
    and WITHOUT ROWID tables with single or composite primary keys.
    """
    escaped = escape_identifier(table_name)
    # Check if table exists
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?;", (table_name,)
    ).fetchone()
    if not exists:
        raise UnsupportedTableStructureError(
            f"Table '{table_name}' does not exist in sqlite_master."
        )

    # Inspect table_info for user column names and declared PRIMARY KEY columns
    info_rows = conn.execute(f"PRAGMA table_info({escaped});").fetchall()
    # columns: (cid, name, type, notnull, dflt_value, pk)
    user_cols_lower = {str(r[1]).lower() for r in info_rows}
    pk_rows = sorted([r for r in info_rows if r[5] > 0], key=lambda r: r[5])
    declared_pk_cols = tuple(str(r[1]) for r in pk_rows)

    # Check candidates for unshadowed physical rowid access
    # SQLite rowid aliases: _rowid_, rowid, oid
    rowid_alias: str | None = None
    for candidate in ("_rowid_", "rowid", "oid"):
        if candidate.lower() not in user_cols_lower:
            try:
                conn.execute(f"SELECT {candidate} FROM {escaped} LIMIT 0;")
                rowid_alias = candidate
                break
            except sqlite3.OperationalError:
                # Table is WITHOUT ROWID or does not allow this alias
                pass

    if rowid_alias is not None:
        # Return True and the specific unshadowed alias used to access the physical rowid
        return True, (rowid_alias,)

    # If rowid cannot be accessed (either WITHOUT ROWID or all aliases shadowed by user columns),
    # fallback to declared PRIMARY KEY
    if declared_pk_cols:
        return False, declared_pk_cols

    # No accessible physical rowid and no declared primary key
    if all(alias in user_cols_lower for alias in ("rowid", "_rowid_", "oid")):
        raise UnsupportedTableStructureError(
            f"Table '{table_name}' shadows 'rowid', '_rowid_', and 'oid' with user columns and lacks a PRIMARY KEY. "
            "Cannot deterministically verify table data."
        )

    raise UnsupportedTableStructureError(
        f"Table '{table_name}' has no stable row identity (neither accessible rowid nor declared PRIMARY KEY). "
        "Cannot deterministically verify table data."
    )


def fingerprint_table_and_columns(
    conn: sqlite3.Connection,
    table_name: str,
    columns: Sequence[str],
    *,
    batch_size: int = 1024,
) -> tuple[str, dict[str, str]]:
    """Compute whole-table SHA-256 and row-identity-bound per-column SHA-256s in a single streaming pass."""
    if not columns:
        empty_digest = hashlib.sha256(b"").hexdigest()
        return empty_digest, {}

    escaped_table = escape_identifier(table_name)
    has_rowid, pk_cols = get_table_identity_info(conn, table_name)

    escaped_data_cols = [escape_identifier(c) for c in columns]
    data_proj = ", ".join(escaped_data_cols)

    if has_rowid:
        rowid_col = pk_cols[0] if pk_cols else "_rowid_"
        query = f'SELECT {rowid_col}, {data_proj} FROM {escaped_table} ORDER BY {rowid_col} ASC;'
        pk_count = 1
        is_rowid_table = True
    else:
        escaped_pk_cols = [escape_identifier(c) for c in pk_cols]
        pk_proj = ", ".join(escaped_pk_cols)
        order_clause = ", ".join(f"{c} ASC" for c in escaped_pk_cols)
        query = f"SELECT {pk_proj}, {data_proj} FROM {escaped_table} ORDER BY {order_clause};"
        pk_count = len(pk_cols)
        is_rowid_table = False

    cursor = conn.execute(query)
    table_hasher = hashlib.sha256()
    col_hashers = [hashlib.sha256() for _ in columns]

    while True:
        batch = cursor.fetchmany(batch_size)
        if not batch:
            break
        for row in batch:
            if is_rowid_table:
                row_id_bytes = b"R:" + canonical_cell_bytes(row[0])
                cells = row[1:]
            else:
                pk_bytes = b"".join(canonical_cell_bytes(cell) for cell in row[:pk_count])
                row_id_bytes = b"PK:" + pk_bytes
                cells = row[pk_count:]

            table_hasher.update(row_id_bytes)
            for idx, cell in enumerate(cells):
                cb = canonical_cell_bytes(cell)
                table_hasher.update(cb)
                # Concatenate row identity with cell bytes so column hashes detect row identity swaps
                col_hashers[idx].update(row_id_bytes + b":" + cb + b";\n")
            table_hasher.update(b"\n")

    col_digests = {
        col_name: col_hashers[idx].hexdigest()
        for idx, col_name in enumerate(columns)
    }
    return table_hasher.hexdigest(), col_digests


def compute_file_sha256(path: Path) -> str:
    """Compute the physical SHA-256 digest of a file in 1 MB chunks."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_logical_db_digest(
    db_path_or_conn: Path | str | sqlite3.Connection,
    *,
    busy_timeout_ms: int = 3000,
) -> str:
    """Compute a deterministic logical SHA-256 digest of database schema objects and table contents.

    Hashes canonical sqlite_master entries and logical table fingerprints under a read transaction,
    ensuring WAL checkpoints never cause false CAS aborts.
    """
    if isinstance(db_path_or_conn, sqlite3.Connection):
        conn = db_path_or_conn
        should_close = False
    else:
        conn = open_hardened_sqlite(db_path_or_conn, busy_timeout_ms=busy_timeout_ms, read_only=True)
        should_close = True

    try:
        hasher = hashlib.sha256()
        master_rows = conn.execute(
            """
            SELECT type, name, tbl_name, COALESCE(sql, '')
            FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%'
            ORDER BY type, name;
            """
        ).fetchall()
        for obj_type, name, tbl_name, sql in master_rows:
            hasher.update(f"M:{obj_type}:{name}:{tbl_name}:{sql}\n".encode())

        # Snapshot all user tables
        table_rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
            """
        ).fetchall()

        for (tbl_name,) in table_rows:
            escaped = escape_identifier(tbl_name)
            col_info = conn.execute(f"PRAGMA table_info({escaped});").fetchall()
            col_names = tuple(r[1] for r in col_info)
            count_row = conn.execute(f"SELECT COUNT(*) FROM {escaped};").fetchone()
            row_count = count_row[0] if count_row else 0
            content_digest, col_digests = fingerprint_table_and_columns(conn, tbl_name, col_names)

            hasher.update(f"T:{tbl_name}:{row_count}:{col_names}:{content_digest}\n".encode())
            for c in sorted(col_digests.keys()):
                hasher.update(f"C:{tbl_name}:{c}:{col_digests[c]}\n".encode())

        return hasher.hexdigest()
    finally:
        if should_close:
            conn.close()
