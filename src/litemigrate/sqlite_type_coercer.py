from typing import Any

class SqliteTypeCoercer:
    @staticmethod
    def coerce_for_storage(val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, bool):
            return 1 if val else 0
        if isinstance(val, (int, float, str, bytes)):
            return val
        return str(val)
