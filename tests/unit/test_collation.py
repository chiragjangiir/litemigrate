from litemigrate.collation import is_valid_sqlite_collation

def test_is_valid_sqlite_collation():
    assert is_valid_sqlite_collation("NOCASE") is True
    assert is_valid_sqlite_collation("binary") is True
    assert is_valid_sqlite_collation("RTRIM") is True
    assert is_valid_sqlite_collation("CUSTOM_LATIN") is False
    assert is_valid_sqlite_collation("") is False
