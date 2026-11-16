import pytest
from litemigrate.safe_drop import generate_safe_table_drop

def test_generate_safe_table_drop():
    sql = generate_safe_table_drop("users")
    assert sql == 'DROP TABLE IF EXISTS "users";'

def test_generate_safe_table_drop_cascade():
    sql = generate_safe_table_drop("users", cascade_foreign_keys=True)
    assert "PRAGMA foreign_keys = OFF;" in sql
    assert 'DROP TABLE IF EXISTS "users";' in sql
    assert "PRAGMA foreign_keys = ON;" in sql

def test_invalid_table_name_rejected():
    with pytest.raises(ValueError):
        generate_safe_table_drop("users; DROP TABLE accounts;--")
