import sqlite3
from litemigrate.database_page_integrity_checker import DatabasePageIntegrityChecker

def test_integrity_checker():
    conn = sqlite3.connect(":memory:")
    res = DatabasePageIntegrityChecker.check_integrity(conn)
    assert res == ["ok"]
