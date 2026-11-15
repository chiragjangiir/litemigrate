"""
Schema difference calculator comparing tables and columns before and after migration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class SchemaDiff:
    added_tables: tuple[str, ...]
    dropped_tables: tuple[str, ...]
    common_tables: tuple[str, ...]

    @classmethod
    def compute(
        cls,
        tables_before: Sequence[str],
        tables_after: Sequence[str],
    ) -> SchemaDiff:
        before_set = set(tables_before)
        after_set = set(tables_after)

        added = tuple(sorted(after_set - before_set))
        dropped = tuple(sorted(before_set - after_set))
        common = tuple(sorted(before_set & after_set))

        return cls(added_tables=added, dropped_tables=dropped, common_tables=common)
