import re
from typing import Dict

class TableCollateParser:
    COLLATE_REGEX = re.compile(r"(\w+)\s+[^,\)]*COLLATE\s+(\w+)", re.IGNORECASE)

    @classmethod
    def parse_collations(cls, ddl: str) -> Dict[str, str]:
        res = {}
        for match in cls.COLLATE_REGEX.finditer(ddl):
            col, collation = match.groups()
            res[col] = collation.upper()
        return res
