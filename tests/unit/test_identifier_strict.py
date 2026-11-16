from litemigrate.validators import validate_identifier_strict

def test_valid_identifiers():
    assert validate_identifier_strict("users") is True
    assert validate_identifier_strict("user_accounts_v2") is True
    assert validate_identifier_strict("_internal_id") is True

def test_sqlite_keywords_rejected():
    assert validate_identifier_strict("order") is False
    assert validate_identifier_strict("TABLE") is False
    assert validate_identifier_strict("group") is False
    assert validate_identifier_strict("sqlite_master") is False
    assert validate_identifier_strict("123bad") is False
    assert validate_identifier_strict("") is False
