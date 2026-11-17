import sqlite3
from litemigrate.collation_registry import register_case_insensitive_collation

def test_register_collation():
    conn = sqlite3.connect(":memory:")
    assert register_case_insensitive_collation(conn) is True
