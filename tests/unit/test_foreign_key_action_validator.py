from litemigrate.foreign_key_action_validator import ForeignKeyActionValidator

def test_foreign_key_action_validator():
    assert ForeignKeyActionValidator.is_valid_action("CASCADE") is True
    assert ForeignKeyActionValidator.is_valid_action("SET NULL") is True
    assert ForeignKeyActionValidator.is_valid_action("INVALID") is False
