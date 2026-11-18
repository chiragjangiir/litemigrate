import sqlite3
from litemigrate.pragma_integrity_checker import check_database_integrity_fast

def test_integrity_quick_check():
    conn = sqlite3.connect(":memory:")
    assert check_database_integrity_fast(conn) is True
