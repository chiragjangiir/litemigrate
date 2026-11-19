from datetime import datetime, timezone
from typing import Optional

class SqliteDatetimeParser:
    @staticmethod
    def parse_to_epoch(dt_str: str) -> Optional[int]:
        if not dt_str:
            return None
        clean = dt_str.strip().replace(" ", "T")
        try:
            if clean.endswith("Z"):
                clean = clean[:-1] + "+00:00"
            dt = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            return None
