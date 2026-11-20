import hashlib
import re

class SqliteStatementHasher:
    @staticmethod
    def hash_statement(sql: str) -> str:
        if not sql:
            return ""
        norm = re.sub(r"\s+", " ", sql).strip().lower()
        return hashlib.sha256(norm.encode("utf-8")).hexdigest()
