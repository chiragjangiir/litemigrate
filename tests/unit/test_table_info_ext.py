import sqlite3
from litemigrate.table_info import parse_pragma_table_info_extended

def test_parse_pragma_table_info_extended():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price REAL DEFAULT 0.0);")
    cols = parse_pragma_table_info_extended(conn, "items")
    assert len(cols) == 3
    assert cols[0]["name"] == "id"
    assert cols[0]["pk"] == 1
    assert cols[1]["name"] == "name"
    assert cols[1]["notnull"] is True
    conn.close()
