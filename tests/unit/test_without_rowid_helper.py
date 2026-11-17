import sqlite3
from litemigrate.without_rowid_helper import is_without_rowid

def test_without_rowid():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE w (id INT PRIMARY KEY, name TEXT) WITHOUT ROWID;")
    assert is_without_rowid(conn, "w") is True
