import sqlite3
from litemigrate.table_row_hasher import TableRowHasher

def test_hash_rows():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INT, name TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
    conn.commit()
    h1 = TableRowHasher.hash_rows(conn, "users", "id ASC")
    h2 = TableRowHasher.hash_rows(conn, "users", "id ASC")
    assert h1 == h2
    assert len(h1) == 64
