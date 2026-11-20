from typing import Any

class ColumnAffinityCoercer:
    @staticmethod
    def determine_affinity(declared_type: str) -> str:
        if not declared_type:
            return "BLOB"
        t = declared_type.upper()
        if "INT" in t:
            return "INTEGER"
        if "CHAR" in t or "CLOB" in t or "TEXT" in t:
            return "TEXT"
        if "BLOB" in t:
            return "BLOB"
        if "REAL" in t or "FLOA" in t or "DOUB" in t:
            return "REAL"
        return "NUMERIC"
