import sqlite3
from litemigrate.strict_table_checker import is_strict_table

def test_strict_table():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE s (id INT) STRICT;")
    conn.execute("CREATE TABLE ns (id INT);")
    assert is_strict_table(conn, "s") is True
    assert is_strict_table(conn, "ns") is False
