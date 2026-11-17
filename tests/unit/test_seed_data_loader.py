import sqlite3
from litemigrate.seed_data_loader import bulk_insert

def test_bulk_insert():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE items (id INT, name TEXT);")
    count = bulk_insert(conn, "items", [{"id": 1, "name": "one"}, {"id": 2, "name": "two"}])
    assert count == 2
