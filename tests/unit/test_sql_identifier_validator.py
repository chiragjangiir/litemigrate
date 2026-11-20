from litemigrate.sql_identifier_validator import SqlIdentifierValidator

def test_identifier_validator():
    assert SqlIdentifierValidator.is_safe_identifier("users_v2") is True
    assert SqlIdentifierValidator.is_safe_identifier("123bad") is False
    assert SqlIdentifierValidator.is_safe_identifier("users;drop table;") is False
