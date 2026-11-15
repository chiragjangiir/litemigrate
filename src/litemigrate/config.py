"""
Configuration management for LiteMigrate.
Loads settings from environment variables or dictionary overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LiteMigrateConfig:
    timeout_seconds: float = 10.0
    default_strategy: str = "auto"
    backup_dir: Path | None = None
    enforce_foreign_keys: bool = True
    wal_mode_preferred: bool = True
    max_memory_mb: int = 64

    @classmethod
    def from_env(cls) -> LiteMigrateConfig:
        timeout = float(os.getenv("LITEMIGRATE_TIMEOUT", "10.0"))
        strategy = os.getenv("LITEMIGRATE_STRATEGY", "auto")
        backup_str = os.getenv("LITEMIGRATE_BACKUP_DIR")
        backup_dir = Path(backup_str) if backup_str else None
        fk = os.getenv("LITEMIGRATE_ENFORCE_FK", "1").lower() in ("1", "true", "yes")
        wal = os.getenv("LITEMIGRATE_WAL", "1").lower() in ("1", "true", "yes")
        mem = int(os.getenv("LITEMIGRATE_MAX_MEMORY_MB", "64"))

        return cls(
            timeout_seconds=timeout,
            default_strategy=strategy,
            backup_dir=backup_dir,
            enforce_foreign_keys=fk,
            wal_mode_preferred=wal,
            max_memory_mb=mem,
        )
