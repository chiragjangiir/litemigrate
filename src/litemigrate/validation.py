"""Schema and data validation engine, invariant auditing, and integrity checks."""

from __future__ import annotations

import re
import sqlite3

from litemigrate.fingerprint import fingerprint_table_and_columns
from litemigrate.models import SchemaObjectSnapshot, TableSnapshot, ValidationVerdict
from litemigrate.policy import MigrationPolicy
from litemigrate.sqlite_backend import escape_identifier


def normalize_sql(sql: str | None) -> str:
    """Normalize whitespace and formatting in DDL statements for robust comparison."""
    if not sql:
        return ""
    return re.sub(r"\s+", " ", sql).strip().rstrip(";")


def snapshot_database_tables(conn: sqlite3.Connection) -> dict[str, TableSnapshot]:
    """Capture table snapshots (row count, columns, whole-table hash, per-column hashes)."""
    cur = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
    )
    table_names = [row[0] for row in cur.fetchall()]
    snapshots: dict[str, TableSnapshot] = {}

    for tbl in table_names:
        escaped = escape_identifier(tbl)
        info_cur = conn.execute(f"PRAGMA table_info({escaped});")
        columns = tuple(row[1] for row in info_cur.fetchall())
        count_cur = conn.execute(f"SELECT COUNT(*) FROM {escaped};")
        count_res = count_cur.fetchone()
        row_count = count_res[0] if count_res else 0

        content_sha, col_shas = fingerprint_table_and_columns(conn, tbl, columns)
        snapshots[tbl] = TableSnapshot(
            name=tbl,
            row_count=row_count,
            column_names=columns,
            content_sha256=content_sha,
            column_sha256s=col_shas,
        )

    return snapshots


def snapshot_schema_objects(conn: sqlite3.Connection) -> dict[str, SchemaObjectSnapshot]:
    """Capture non-table schema objects (indexes, triggers, and views)."""
    cur = conn.execute(
        """
        SELECT name, type, tbl_name, sql
        FROM sqlite_master
        WHERE type IN ('index', 'trigger', 'view') AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name;
        """
    )
    objects: dict[str, SchemaObjectSnapshot] = {}
    for name, obj_type, tbl_name, sql in cur.fetchall():
        objects[name] = SchemaObjectSnapshot(
            name=name,
            obj_type=obj_type,
            tbl_name=tbl_name or "",
            sql=normalize_sql(sql),
        )
    return objects


def validate_foreign_keys(conn: sqlite3.Connection) -> list[str]:
    """Run PRAGMA foreign_key_check and return violations."""
    cur = conn.execute("PRAGMA foreign_key_check;")
    violations: list[str] = []
    for row in cur.fetchall():
        # format: (table, rowid, parent_table, fkid)
        tbl = row[0]
        rowid = row[1]
        parent = row[2]
        fkid = row[3]
        violations.append(
            f"Table '{tbl}' rowid {rowid} violates foreign key constraint #{fkid} referencing parent '{parent}'"
        )
    return violations


def validate_database_integrity(conn: sqlite3.Connection) -> tuple[bool, list[str]]:
    """Run PRAGMA integrity_check and return whether database structure is valid."""
    cur = conn.execute("PRAGMA integrity_check;")
    rows = [r[0] for r in cur.fetchall()]
    if rows == ["ok"]:
        return True, []
    return False, rows


def validate_surviving_views(conn: sqlite3.Connection) -> list[str]:
    """Verify that all surviving views can still be parsed and executed."""
    view_cur = conn.execute("SELECT name FROM sqlite_master WHERE type = 'view';")
    errors: list[str] = []
    for (view_name,) in view_cur.fetchall():
        try:
            conn.execute(f"SELECT * FROM {escape_identifier(view_name)} LIMIT 0;")
        except sqlite3.OperationalError as exc:
            errors.append(f"Surviving view '{view_name}' is invalid after migration: {exc}")
    return errors


def evaluate_migration_diff(
    tables_before: dict[str, TableSnapshot],
    tables_after: dict[str, TableSnapshot],
    schema_before: dict[str, SchemaObjectSnapshot],
    schema_after: dict[str, SchemaObjectSnapshot],
    policy: MigrationPolicy,
    shadow_conn: sqlite3.Connection,
) -> tuple[
    ValidationVerdict,
    list[str],
    list[str],
    list[str],
    list[str],
    list[SchemaObjectSnapshot],
    list[str],
    bool,
    list[str],
]:
    """Evaluate all safety invariants against the before/after snapshots and policy."""
    details: list[str] = []

    # 1. Check dropped tables
    dropped_tables: list[str] = []
    for tbl in tables_before:
        if tbl not in tables_after:
            dropped_tables.append(tbl)
            if tbl not in policy.allowed_dropped_tables:
                details.append(
                    f"Unexpected dropped table '{tbl}' was not declared in policy.allowed_dropped_tables."
                )

    if details:
        return (
            ValidationVerdict.BLOCKED_UNEXPECTED_TABLE_DROP,
            details,
            dropped_tables,
            [],
            [],
            [],
            [],
            True,
            [],
        )

    # 2. Check foreign keys first (finding S-04 / D-04: FK check before integrity and mutations)
    fk_violations = validate_foreign_keys(shadow_conn)
    if fk_violations:
        return (
            ValidationVerdict.BLOCKED_FOREIGN_KEY_VIOLATION,
            fk_violations,
            dropped_tables,
            [],
            [],
            [],
            fk_violations,
            True,
            [],
        )

    # 3. Check row losses and mutations
    row_loss_tables: list[str] = []
    mutated_tables: list[str] = []

    for tbl, snap_before in tables_before.items():
        if tbl not in tables_after:
            continue
        snap_after = tables_after[tbl]

        # Row loss check
        if snap_after.row_count < snap_before.row_count:
            row_loss_tables.append(tbl)
            if tbl not in policy.allowed_row_loss_tables:
                details.append(
                    f"Table '{tbl}' lost rows ({snap_before.row_count} -> {snap_after.row_count}) "
                    "without declaration in policy.allowed_row_loss_tables."
                )

        # Mutation check
        if snap_after.column_names == snap_before.column_names:
            if (
                snap_after.row_count == snap_before.row_count
                and snap_after.content_sha256 != snap_before.content_sha256
                and tbl not in policy.allowed_mutated_tables
            ):
                mutated_tables.append(tbl)
                details.append(
                    f"Table '{tbl}' data was modified without declaration in policy.allowed_mutated_tables."
                )
        else:
            # Columns changed (added/dropped/reordered). Check shared columns using per-column digests!
            shared_cols = set(snap_before.column_sha256s.keys()) & set(snap_after.column_sha256s.keys())
            mutated_cols = [
                c for c in shared_cols
                if snap_before.column_sha256s[c] != snap_after.column_sha256s[c]
            ]
            if (
                mutated_cols
                and tbl not in policy.allowed_mutated_tables
                and tbl not in policy.allowed_row_loss_tables
            ):
                mutated_tables.append(tbl)
                details.append(
                    f"Table '{tbl}' existing column(s) {mutated_cols} mutated during column modification "
                    "without declaration in policy.allowed_mutated_tables."
                )

    if any("lost rows" in d for d in details):
        return (
            ValidationVerdict.BLOCKED_UNEXPECTED_ROW_LOSS,
            details,
            dropped_tables,
            mutated_tables,
            row_loss_tables,
            [],
            [],
            True,
            [],
        )

    if any("modified" in d or "mutated" in d for d in details):
        return (
            ValidationVerdict.BLOCKED_UNEXPECTED_DATA_MUTATION,
            details,
            dropped_tables,
            mutated_tables,
            row_loss_tables,
            [],
            [],
            True,
            [],
        )

    # 4. Check dropped schema objects (views, triggers, indexes)
    dropped_schema_objs: list[SchemaObjectSnapshot] = []
    for name, obj in schema_before.items():
        if name not in schema_after:
            dropped_schema_objs.append(obj)
            allowed = False
            if obj.obj_type == "view" and name in policy.allowed_dropped_views or obj.obj_type == "trigger" and name in policy.allowed_dropped_triggers or obj.obj_type == "index" and name in policy.allowed_dropped_indexes:
                allowed = True

            if not allowed:
                details.append(
                    f"Unexpected dropped {obj.obj_type} '{name}' on table '{obj.tbl_name}' "
                    "was not declared in policy."
                )

    if details:
        return (
            ValidationVerdict.BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP,
            details,
            dropped_tables,
            mutated_tables,
            row_loss_tables,
            dropped_schema_objs,
            [],
            True,
            [],
        )

    # 5. Check surviving views
    view_errors = validate_surviving_views(shadow_conn)
    if view_errors:
        return (
            ValidationVerdict.BLOCKED_INTEGRITY_FAILURE,
            view_errors,
            dropped_tables,
            mutated_tables,
            row_loss_tables,
            dropped_schema_objs,
            [],
            False,
            view_errors,
        )

    # 6. Check database integrity
    integrity_ok, integrity_errors = validate_database_integrity(shadow_conn)
    if not integrity_ok:
        return (
            ValidationVerdict.BLOCKED_INTEGRITY_FAILURE,
            integrity_errors,
            dropped_tables,
            mutated_tables,
            row_loss_tables,
            dropped_schema_objs,
            [],
            False,
            integrity_errors,
        )

    details.append("Shadow validation passed: all schema, data, foreign key, and integrity invariants satisfied.")
    return (
        ValidationVerdict.PASSED,
        details,
        dropped_tables,
        mutated_tables,
        row_loss_tables,
        dropped_schema_objs,
        [],
        True,
        [],
    )
