"""Standardized SQLite primary error codes and descriptions."""
from __future__ import annotations

SQLITE_OK = 0
SQLITE_ERROR = 1
SQLITE_BUSY = 5
SQLITE_LOCKED = 6
SQLITE_READONLY = 8
SQLITE_CORRUPT = 11

ERROR_DESCRIPTIONS = {
    SQLITE_BUSY: "Database engine was unable to acquire database lock",
    SQLITE_LOCKED: "Lock conflict has occurred in another connection",
    SQLITE_CORRUPT: "Database disk image is malformed",
}
