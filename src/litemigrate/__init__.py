"""LiteMigrate — Safer SQLite migrations through shadow verification."""

from __future__ import annotations

__version__ = "0.1.0a1"

from litemigrate.engine import LiteMigrateEngine
from litemigrate.exceptions import (
    ConcurrencyConflictError,
    LiteMigrateError,
    LockTimeoutError,
    MigrationExecutionError,
    SecurityError,
    UnsupportedMigrationTypeError,
    UnsupportedTableStructureError,
    ValidationFailureError,
)
from litemigrate.models import (
    AuditReport,
    CloneStrategy,
    DatabaseInspectionReport,
    SchemaObjectSnapshot,
    ShadowCloneResult,
    TableSnapshot,
    ValidationVerdict,
)
from litemigrate.policy import MigrationPolicy

__all__ = [
    "AuditReport",
    "CloneStrategy",
    "ConcurrencyConflictError",
    "DatabaseInspectionReport",
    "LiteMigrateEngine",
    "LiteMigrateError",
    "LockTimeoutError",
    "MigrationExecutionError",
    "MigrationPolicy",
    "SchemaObjectSnapshot",
    "SecurityError",
    "ShadowCloneResult",
    "TableSnapshot",
    "UnsupportedMigrationTypeError",
    "UnsupportedTableStructureError",
    "ValidationFailureError",
    "ValidationVerdict",
    "__version__",
]
