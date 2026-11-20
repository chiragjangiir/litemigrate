from litemigrate.strict_mode_ddl_validator import StrictModeDdlValidator

def test_strict_mode_validator():
    assert StrictModeDdlValidator.validate_strict_column("TEXT") is True
    assert StrictModeDdlValidator.validate_strict_column("INT") is True
    assert StrictModeDdlValidator.validate_strict_column("VARCHAR") is False
