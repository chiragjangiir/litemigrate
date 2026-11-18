import sqlite3
from litemigrate.sqlite_limits import get_max_page_count

def test_max_page_count():
    conn = sqlite3.connect(":memory:")
    count = get_max_page_count(conn)
    assert count > 0
