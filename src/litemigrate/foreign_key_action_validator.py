from typing import Set

class ForeignKeyActionValidator:
    ACTIONS: Set[str] = {"NO ACTION", "RESTRICT", "SET NULL", "SET DEFAULT", "CASCADE"}

    @classmethod
    def is_valid_action(cls, action: str) -> bool:
        if not action:
            return False
        return action.strip().upper() in cls.ACTIONS
