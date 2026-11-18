import sqlite3
from litemigrate.database_freelist_inspector import get_freelist_count

def test_freelist_count():
    conn = sqlite3.connect(":memory:")
    assert get_freelist_count(conn) >= 0
