"""Unified LiteMigrate engine coordinating inspection, shadow validation, and atomic promotion."""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path

from litemigrate.cloning import create_shadow_database, reject_symlink
from litemigrate.exceptions import (
    ConcurrencyConflictError,
    LockTimeoutError,
    UnsupportedMigrationTypeError,
)
from litemigrate.fingerprint import (
    compute_file_sha256,
    compute_logical_db_digest,
)
from litemigrate.models import (
    AuditReport,
    CloneStrategy,
    DatabaseInspectionReport,
    ValidationVerdict,
)
from litemigrate.policy import MigrationPolicy
from litemigrate.promotion import promote_shadow_to_source
from litemigrate.sqlite_backend import (
    cleanup_db_artifacts,
    open_hardened_sqlite,
    split_sql_statements,
)
from litemigrate.validation import (
    evaluate_migration_diff,
    snapshot_database_tables,
    snapshot_schema_objects,
    validate_database_integrity,
)

logger = logging.getLogger("litemigrate.engine")


class LiteMigrateEngine:
    """Core orchestration engine for SQLite shadow migration safety."""

    @staticmethod
    def inspect(db_path: Path | str) -> DatabaseInspectionReport:
        """Inspect a SQLite database, returning schema and integrity metadata without exposing row contents."""
        p = Path(db_path).resolve()
        reject_symlink(p)
        if not p.exists():
            raise FileNotFoundError(f"Database file not found: {p}")

        conn = open_hardened_sqlite(p, read_only=True)
        try:
            ver_row = conn.execute("SELECT sqlite_version();").fetchone()
            sqlite_ver = ver_row[0] if ver_row else "unknown"

            jmode_row = conn.execute("PRAGMA journal_mode;").fetchone()
            journal_mode = jmode_row[0].upper() if jmode_row else "UNKNOWN"

            fk_row = conn.execute("PRAGMA foreign_keys;").fetchone()
            fks_enabled = bool(fk_row[0]) if fk_row else False

            tbl_rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
            ).fetchall()
            tables = tuple(r[0] for r in tbl_rows)

            schema_rows = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type IN ('index', 'trigger', 'view') AND name NOT LIKE 'sqlite_%';"
            ).fetchone()
            schema_count = schema_rows[0] if schema_rows else 0

            integrity_ok, integrity_errs = validate_database_integrity(conn)
            integrity_msg = "ok" if integrity_ok else "; ".join(integrity_errs)

            return DatabaseInspectionReport(
                path=str(p),
                sqlite_version=sqlite_ver,
                file_size_bytes=p.stat().st_size,
                journal_mode=journal_mode,
                table_count=len(tables),
                tables=tables,
                schema_object_count=schema_count,
                foreign_keys_enabled=fks_enabled,
                integrity_ok=integrity_ok,
                integrity_message=integrity_msg,
            )
        finally:
            conn.close()

    @classmethod
    def execute_and_validate(
        cls,
        source_db: Path | str,
        migration_sql: str | Sequence[str] | Path,
        *,
        policy: MigrationPolicy | None = None,
        clone_strategy: CloneStrategy = CloneStrategy.AUTO,
        apply_to_source_on_pass: bool = False,
        confirmed: bool = False,
    ) -> AuditReport:
        """Execute migration on an isolated shadow copy, audit invariants, and optionally promote."""
        t_start = time.perf_counter()
        source_path = Path(source_db).resolve()
        reject_symlink(source_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Source database not found: {source_path}")

        # Check for callable migration rejection (Gap A)
        if callable(migration_sql):
            empty_snap: dict = {}
            return AuditReport(
                verdict=ValidationVerdict.BLOCKED_UNSUPPORTED_MIGRATION_TYPE,
                details=(
                    "Unsupported migration type: Python callables are explicitly rejected by LiteMigrate "
                    "for safety. Migrations must be provided as SQL script strings or files.",
                ),
                original_db_path=source_path,
                original_db_sha256_before="",
                original_db_sha256_after="",
                original_db_untouched=True,
                promoted_to_source=False,
                backup_path=None,
                clone_result=None,
                tables_before=empty_snap,
                tables_after=empty_snap,
                dropped_tables=(),
                mutated_tables=(),
                row_loss_tables=(),
                dropped_schema_objects=(),
                foreign_key_violations=(),
                integrity_check_passed=False,
                integrity_errors=("Callable migration rejected.",),
                migration_duration_ms=0.0,
                audit_duration_ms=0.0,
                total_elapsed_ms=0.0,
            )

        active_policy = policy or MigrationPolicy()
        raw_sql_script = cls._resolve_migration_sql(migration_sql)

        # Baseline file sha256
        source_sha256_before = compute_file_sha256(source_path)

        # Create isolated workspace directory with 0o700 permissions
        temp_dir = Path(tempfile.mkdtemp(prefix="litemigrate_run_"))
        os.chmod(temp_dir, 0o700)

        clone_result = None
        shadow_path: Path | None = None
        try:
            # 1. Create Shadow Database
            try:
                clone_result = create_shadow_database(
                    source_path,
                    strategy=clone_strategy,
                    busy_timeout_ms=active_policy.busy_timeout_ms,
                    temp_dir=temp_dir,
                )
                shadow_path = clone_result.shadow_path
            except sqlite3.OperationalError as exc:
                empty_snap = {}
                return AuditReport(
                    verdict=ValidationVerdict.BLOCKED_CONCURRENT_LOCK,
                    details=(f"Shadow database creation blocked by database lock: {exc}",),
                    original_db_path=source_path,
                    original_db_sha256_before=source_sha256_before,
                    original_db_sha256_after=source_sha256_before,
                    original_db_untouched=True,
                    promoted_to_source=False,
                    backup_path=None,
                    clone_result=None,
                    tables_before=empty_snap,
                    tables_after=empty_snap,
                    dropped_tables=(),
                    mutated_tables=(),
                    row_loss_tables=(),
                    dropped_schema_objects=(),
                    foreign_key_violations=(),
                    integrity_check_passed=False,
                    integrity_errors=(str(exc),),
                    migration_duration_ms=0.0,
                    audit_duration_ms=0.0,
                    total_elapsed_ms=(time.perf_counter() - t_start) * 1000.0,
                )

            # 2. Capture Pre-Migration Baseline purely from consistent shadow copy
            shadow_conn = open_hardened_sqlite(
                shadow_path,
                busy_timeout_ms=active_policy.busy_timeout_ms,
                isolation_level=None,
            )
            try:
                shadow_baseline_digest = compute_logical_db_digest(shadow_conn)
                tables_before = snapshot_database_tables(shadow_conn)
                schema_before = snapshot_schema_objects(shadow_conn)

                # 3. Execute Migration Statements on Shadow Database
                t_mig_start = time.perf_counter()
                statements = split_sql_statements(raw_sql_script)

                fk_flag = 0 if active_policy.disable_foreign_keys_during_migration else 1
                shadow_conn.execute(f"PRAGMA foreign_keys = {fk_flag};")
                shadow_conn.execute("BEGIN IMMEDIATE;")
                try:
                    for stmt in statements:
                        shadow_conn.execute(stmt)
                    shadow_conn.execute("COMMIT;")
                except Exception as exc:
                    if shadow_conn.in_transaction:
                        try:
                            shadow_conn.execute("ROLLBACK;")
                        except sqlite3.Error:
                            pass
                    tables_after = snapshot_database_tables(shadow_conn)
                    migration_duration_ms = (time.perf_counter() - t_mig_start) * 1000.0
                    return AuditReport(
                        verdict=ValidationVerdict.BLOCKED_MIGRATION_EXCEPTION,
                        details=(f"Migration SQL execution failed on shadow database: {exc}",),
                        original_db_path=source_path,
                        original_db_sha256_before=source_sha256_before,
                        original_db_sha256_after=source_sha256_before,
                        original_db_untouched=True,
                        promoted_to_source=False,
                        backup_path=None,
                        clone_result=clone_result,
                        tables_before=tables_before,
                        tables_after=tables_after,
                        dropped_tables=(),
                        mutated_tables=(),
                        row_loss_tables=(),
                        dropped_schema_objects=(),
                        foreign_key_violations=(),
                        integrity_check_passed=False,
                        integrity_errors=(str(exc),),
                        migration_duration_ms=migration_duration_ms,
                        audit_duration_ms=0.0,
                        total_elapsed_ms=(time.perf_counter() - t_start) * 1000.0,
                    )
                finally:
                    try:
                        shadow_conn.execute("PRAGMA foreign_keys = ON;")
                    except sqlite3.Error:
                        pass
                migration_duration_ms = (time.perf_counter() - t_mig_start) * 1000.0

                # 4. Post-Migration Shadow Audit
                t_audit_start = time.perf_counter()
                tables_after = snapshot_database_tables(shadow_conn)
                schema_after = snapshot_schema_objects(shadow_conn)

                (
                    verdict,
                    details,
                    dropped_tables,
                    mutated_tables,
                    row_loss_tables,
                    dropped_schema_objs,
                    fk_violations,
                    integrity_ok,
                    integrity_errors,
                ) = evaluate_migration_diff(
                    tables_before,
                    tables_after,
                    schema_before,
                    schema_after,
                    active_policy,
                    shadow_conn,
                )
                audit_duration_ms = (time.perf_counter() - t_audit_start) * 1000.0
            finally:
                shadow_conn.close()

            # 5. Promotion (if requested and validation passed)
            promoted = False
            backup_file: Path | None = None
            if verdict == ValidationVerdict.PASSED and apply_to_source_on_pass:
                if not confirmed:
                    details = list(details)
                    details.append("Promotion aborted: apply requires explicit confirmation.")
                    verdict = ValidationVerdict.PASSED  # validation passed, but not applied
                else:
                    try:
                        backup_file = promote_shadow_to_source(
                            shadow_path=shadow_path,
                            source_path=source_path,
                            expected_source_digest=shadow_baseline_digest,
                            migration_sql=raw_sql_script,
                            disable_foreign_keys=active_policy.disable_foreign_keys_during_migration,
                            busy_timeout_ms=active_policy.busy_timeout_ms,
                            create_backup=True,
                        )
                        promoted = True
                        details = list(details)
                        details.append(f"Successfully promoted migration to source database (backup at {backup_file}).")
                    except ConcurrencyConflictError as exc:
                        verdict = ValidationVerdict.BLOCKED_SOURCE_MODIFIED_CONCURRENTLY
                        details = [str(exc)]
                    except (LockTimeoutError, sqlite3.OperationalError) as exc:
                        verdict = ValidationVerdict.BLOCKED_CONCURRENT_LOCK
                        details = [str(exc)]

            source_sha256_after = compute_file_sha256(source_path)
            original_untouched = not promoted

            return AuditReport(
                verdict=verdict,
                details=tuple(details),
                original_db_path=source_path,
                original_db_sha256_before=source_sha256_before,
                original_db_sha256_after=source_sha256_after,
                original_db_untouched=original_untouched,
                promoted_to_source=promoted,
                backup_path=backup_file,
                clone_result=clone_result,
                tables_before=tables_before,
                tables_after=tables_after,
                dropped_tables=tuple(dropped_tables),
                mutated_tables=tuple(mutated_tables),
                row_loss_tables=tuple(row_loss_tables),
                dropped_schema_objects=tuple(dropped_schema_objs),
                foreign_key_violations=tuple(fk_violations),
                integrity_check_passed=integrity_ok,
                integrity_errors=tuple(integrity_errors),
                migration_duration_ms=migration_duration_ms,
                audit_duration_ms=audit_duration_ms,
                total_elapsed_ms=(time.perf_counter() - t_start) * 1000.0,
            )
        finally:
            # Deterministic cleanup of temporary workspace
            if shadow_path:
                cleanup_db_artifacts(shadow_path)
            shutil.rmtree(temp_dir, ignore_errors=True)

    @classmethod
    def _resolve_migration_sql(cls, migration: str | Sequence[str] | Path) -> str:
        """Resolve migration parameter into a raw SQL script string."""
        if isinstance(migration, Path):
            with open(migration, "r", encoding="utf-8") as f:
                return f.read()
        if isinstance(migration, str):
            # Check if it's an existing file path
            candidate = Path(migration)
            if candidate.is_file():
                with open(candidate, "r", encoding="utf-8") as f:
                    return f.read()
            return migration
        if isinstance(migration, Sequence):
            return "\n".join(migration)
        raise UnsupportedMigrationTypeError(f"Cannot resolve migration SQL from type {type(migration)}")
