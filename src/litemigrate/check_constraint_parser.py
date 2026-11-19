import re
from typing import List

class CheckConstraintParser:
    CHECK_REGEX = re.compile(r"CHECK\s*\((.+?)\)(?:,|$)", re.IGNORECASE)

    @classmethod
    def extract_checks(cls, table_sql: str) -> List[str]:
        if not table_sql:
            return []
        matches = cls.CHECK_REGEX.findall(table_sql)
        return [m.strip() for m in matches]
