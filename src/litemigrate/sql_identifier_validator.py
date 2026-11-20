import re

class SqlIdentifierValidator:
    IDENT_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    @classmethod
    def is_safe_identifier(cls, name: str) -> bool:
        if not name or len(name) > 128:
            return False
        return bool(cls.IDENT_REGEX.match(name))
