import sqlite3
from litemigrate.sqlite_collations_lister import get_available_collations

def test_collations_list():
    conn = sqlite3.connect(":memory:")
    collations = get_available_collations(conn)
    assert "RTRIM" in collations or "NOCASE" in collations or "BINARY" in collations
