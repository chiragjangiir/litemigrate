import re
from typing import Set

class StrictModeDdlValidator:
    STRICT_TYPES: Set[str] = {"INT", "INTEGER", "REAL", "TEXT", "BLOB", "ANY"}

    @classmethod
    def validate_strict_column(cls, col_type: str) -> bool:
        if not col_type:
            return False
        return col_type.strip().upper() in cls.STRICT_TYPES
