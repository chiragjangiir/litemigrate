"""Migration safety policies and permission declarations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MigrationPolicy:
    """Explicitly declared permissions for destructive or mutating migration changes.

    Default settings are strictly conservative: no tables, rows, columns, views,
    triggers, or indexes may be dropped or unexpectedly mutated without explicit
    declarations in this policy.
    """

    allowed_dropped_tables: frozenset[str] = field(default_factory=frozenset)
    allowed_row_loss_tables: frozenset[str] = field(default_factory=frozenset)
    allowed_mutated_tables: frozenset[str] = field(default_factory=frozenset)
    allowed_dropped_views: frozenset[str] = field(default_factory=frozenset)
    allowed_dropped_triggers: frozenset[str] = field(default_factory=frozenset)
    allowed_dropped_indexes: frozenset[str] = field(default_factory=frozenset)
    disable_foreign_keys_during_migration: bool = True
    busy_timeout_ms: int = 3000

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_dropped_tables": sorted(list(self.allowed_dropped_tables)),
            "allowed_row_loss_tables": sorted(list(self.allowed_row_loss_tables)),
            "allowed_mutated_tables": sorted(list(self.allowed_mutated_tables)),
            "allowed_dropped_views": sorted(list(self.allowed_dropped_views)),
            "allowed_dropped_triggers": sorted(list(self.allowed_dropped_triggers)),
            "allowed_dropped_indexes": sorted(list(self.allowed_dropped_indexes)),
            "disable_foreign_keys_during_migration": self.disable_foreign_keys_during_migration,
            "busy_timeout_ms": self.busy_timeout_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MigrationPolicy:
        return cls(
            allowed_dropped_tables=frozenset(data.get("allowed_dropped_tables", ())),
            allowed_row_loss_tables=frozenset(data.get("allowed_row_loss_tables", ())),
            allowed_mutated_tables=frozenset(data.get("allowed_mutated_tables", ())),
            allowed_dropped_views=frozenset(data.get("allowed_dropped_views", ())),
            allowed_dropped_triggers=frozenset(data.get("allowed_dropped_triggers", ())),
            allowed_dropped_indexes=frozenset(data.get("allowed_dropped_indexes", ())),
            disable_foreign_keys_during_migration=bool(
                data.get("disable_foreign_keys_during_migration", True)
            ),
            busy_timeout_ms=int(data.get("busy_timeout_ms", 3000)),
        )

    @classmethod
    def from_file(cls, path: Path | str) -> MigrationPolicy:
        """Load migration policy from a JSON file."""
        p = Path(path)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def strict(cls, busy_timeout_ms: int = 3000) -> MigrationPolicy:
        """Construct the strictest default policy where zero drops or mutations are permitted."""
        return cls(busy_timeout_ms=busy_timeout_ms)
