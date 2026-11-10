"""LiteMigrate exception hierarchy."""

from __future__ import annotations


class LiteMigrateError(Exception):
    """Base exception for all LiteMigrate operations."""


class UnsupportedMigrationTypeError(LiteMigrateError):
    """Raised when an unsupported migration type (e.g. Python callable) is passed."""


class UnsupportedTableStructureError(LiteMigrateError):
    """Raised when a table cannot be safely or deterministically fingerprinted."""


class ConcurrencyConflictError(LiteMigrateError):
    """Raised when a concurrent writer modifies the source database prior to promotion."""


class LockTimeoutError(LiteMigrateError):
    """Raised when a SQLite or POSIX lock acquisition exceeds the configured deadline."""


class SecurityError(LiteMigrateError):
    """Raised when a symlink, permission, or unsafe path is encountered."""


class MigrationExecutionError(LiteMigrateError):
    """Raised when migration SQL fails execution during shadow migration."""


class ValidationFailureError(LiteMigrateError):
    """Raised when an invariant (foreign key, integrity, or unpermitted mutation) fails."""
