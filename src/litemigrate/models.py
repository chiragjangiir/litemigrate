"""Domain models, enums, snapshots, and audit report structures."""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class CloneStrategy(str, enum.Enum):
    """Supported shadow database creation strategies."""

    AUTO = "auto"
    APFS_CLONEFILE = "apfs_clonefile"
    LINUX_FICLONE = "linux_ficlone"
    SQLITE_BACKUP_API = "sqlite_backup_api"


class ValidationVerdict(str, enum.Enum):
    """Outcome of shadow migration safety validation."""

    PASSED = "passed"
    BLOCKED_UNEXPECTED_ROW_LOSS = "blocked_unexpected_row_loss"
    BLOCKED_UNEXPECTED_DATA_MUTATION = "blocked_unexpected_data_mutation"
    BLOCKED_UNEXPECTED_TABLE_DROP = "blocked_unexpected_table_drop"
    BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP = "blocked_unexpected_schema_object_drop"
    BLOCKED_FOREIGN_KEY_VIOLATION = "blocked_foreign_key_violation"
    BLOCKED_INTEGRITY_FAILURE = "blocked_integrity_failure"
    BLOCKED_MIGRATION_EXCEPTION = "blocked_migration_exception"
    BLOCKED_CONCURRENT_LOCK = "blocked_concurrent_lock"
    BLOCKED_SOURCE_MODIFIED_CONCURRENTLY = "blocked_source_modified_concurrently"
    BLOCKED_UNSUPPORTED_MIGRATION_TYPE = "blocked_unsupported_migration_type"


@dataclass(frozen=True)
class TableSnapshot:
    """Baseline and post-migration fingerprint of a single SQLite table."""

    name: str
    row_count: int
    column_names: tuple[str, ...]
    content_sha256: str
    column_sha256s: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "row_count": self.row_count,
            "column_names": list(self.column_names),
            "content_sha256": self.content_sha256,
            "column_sha256s": dict(self.column_sha256s),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TableSnapshot:
        return cls(
            name=data["name"],
            row_count=data["row_count"],
            column_names=tuple(data["column_names"]),
            content_sha256=data["content_sha256"],
            column_sha256s=data.get("column_sha256s", {}),
        )


@dataclass(frozen=True)
class SchemaObjectSnapshot:
    """Fingerprint of a non-table schema object (index, trigger, or view)."""

    name: str
    obj_type: str
    tbl_name: str
    sql: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "obj_type": self.obj_type,
            "tbl_name": self.tbl_name,
            "sql": self.sql,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchemaObjectSnapshot:
        return cls(
            name=data["name"],
            obj_type=data["obj_type"],
            tbl_name=data["tbl_name"],
            sql=data.get("sql", ""),
        )


@dataclass(frozen=True)
class ShadowCloneResult:
    """Metadata regarding shadow database creation."""

    shadow_path: Path
    strategy_used: CloneStrategy
    duration_ms: float
    wal_required_backup_fallback: bool
    wal_size_bytes_at_clone: int
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "shadow_path": str(self.shadow_path),
            "strategy_used": self.strategy_used.value,
            "duration_ms": round(self.duration_ms, 3),
            "wal_required_backup_fallback": self.wal_required_backup_fallback,
            "wal_size_bytes_at_clone": self.wal_size_bytes_at_clone,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ShadowCloneResult:
        return cls(
            shadow_path=Path(data["shadow_path"]),
            strategy_used=CloneStrategy(data["strategy_used"]),
            duration_ms=float(data["duration_ms"]),
            wal_required_backup_fallback=bool(data["wal_required_backup_fallback"]),
            wal_size_bytes_at_clone=int(data["wal_size_bytes_at_clone"]),
            notes=tuple(data.get("notes", ())),
        )


@dataclass(frozen=True)
class DatabaseInspectionReport:
    """Summary of database properties and schema contents."""

    path: str
    sqlite_version: str
    file_size_bytes: int
    journal_mode: str
    table_count: int
    tables: tuple[str, ...]
    schema_object_count: int
    foreign_keys_enabled: bool
    integrity_ok: bool
    integrity_message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "sqlite_version": self.sqlite_version,
            "file_size_bytes": self.file_size_bytes,
            "journal_mode": self.journal_mode,
            "table_count": self.table_count,
            "tables": list(self.tables),
            "schema_object_count": self.schema_object_count,
            "foreign_keys_enabled": self.foreign_keys_enabled,
            "integrity_ok": self.integrity_ok,
            "integrity_message": self.integrity_message,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass(frozen=True)
class AuditReport:
    """Comprehensive, structured audit report produced after shadow validation."""

    verdict: ValidationVerdict
    details: tuple[str, ...]
    original_db_path: Path
    original_db_sha256_before: str
    original_db_sha256_after: str
    original_db_untouched: bool
    promoted_to_source: bool
    backup_path: Path | None
    clone_result: ShadowCloneResult | None
    tables_before: dict[str, TableSnapshot]
    tables_after: dict[str, TableSnapshot]
    dropped_tables: tuple[str, ...]
    mutated_tables: tuple[str, ...]
    row_loss_tables: tuple[str, ...]
    dropped_schema_objects: tuple[SchemaObjectSnapshot, ...]
    foreign_key_violations: tuple[str, ...]
    integrity_check_passed: bool
    integrity_errors: tuple[str, ...]
    migration_duration_ms: float
    audit_duration_ms: float
    total_elapsed_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "details": list(self.details),
            "original_db_path": str(self.original_db_path),
            "original_db_sha256_before": self.original_db_sha256_before,
            "original_db_sha256_after": self.original_db_sha256_after,
            "original_db_untouched": self.original_db_untouched,
            "promoted_to_source": self.promoted_to_source,
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "clone_result": self.clone_result.to_dict() if self.clone_result else None,
            "tables_before": {k: v.to_dict() for k, v in self.tables_before.items()},
            "tables_after": {k: v.to_dict() for k, v in self.tables_after.items()},
            "dropped_tables": list(self.dropped_tables),
            "mutated_tables": list(self.mutated_tables),
            "row_loss_tables": list(self.row_loss_tables),
            "dropped_schema_objects": [obj.to_dict() for obj in self.dropped_schema_objects],
            "foreign_key_violations": list(self.foreign_key_violations),
            "integrity_check_passed": self.integrity_check_passed,
            "integrity_errors": list(self.integrity_errors),
            "migration_duration_ms": round(self.migration_duration_ms, 3),
            "audit_duration_ms": round(self.audit_duration_ms, 3),
            "total_elapsed_ms": round(self.total_elapsed_ms, 3),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditReport:
        clone_res = (
            ShadowCloneResult.from_dict(data["clone_result"])
            if data.get("clone_result")
            else None
        )
        return cls(
            verdict=ValidationVerdict(data["verdict"]),
            details=tuple(data.get("details", ())),
            original_db_path=Path(data["original_db_path"]),
            original_db_sha256_before=data["original_db_sha256_before"],
            original_db_sha256_after=data["original_db_sha256_after"],
            original_db_untouched=bool(data["original_db_untouched"]),
            promoted_to_source=bool(data.get("promoted_to_source", False)),
            backup_path=Path(data["backup_path"]) if data.get("backup_path") else None,
            clone_result=clone_res,
            tables_before={
                k: TableSnapshot.from_dict(v)
                for k, v in data.get("tables_before", {}).items()
            },
            tables_after={
                k: TableSnapshot.from_dict(v)
                for k, v in data.get("tables_after", {}).items()
            },
            dropped_tables=tuple(data.get("dropped_tables", ())),
            mutated_tables=tuple(data.get("mutated_tables", ())),
            row_loss_tables=tuple(data.get("row_loss_tables", ())),
            dropped_schema_objects=tuple(
                SchemaObjectSnapshot.from_dict(o)
                for o in data.get("dropped_schema_objects", ())
            ),
            foreign_key_violations=tuple(data.get("foreign_key_violations", ())),
            integrity_check_passed=bool(data.get("integrity_check_passed", True)),
            integrity_errors=tuple(data.get("integrity_errors", ())),
            migration_duration_ms=float(data.get("migration_duration_ms", 0.0)),
            audit_duration_ms=float(data.get("audit_duration_ms", 0.0)),
            total_elapsed_ms=float(data.get("total_elapsed_ms", 0.0)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> AuditReport:
        return cls.from_dict(json.loads(json_str))
