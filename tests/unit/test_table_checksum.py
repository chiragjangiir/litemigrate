import sqlite3
from litemigrate.checksum_verify import verify_table_row_checksum

def test_verify_table_row_checksum():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE items (id INT);")
    conn.execute("INSERT INTO items VALUES (1);")
    conn.execute("INSERT INTO items VALUES (2);")
    h1 = verify_table_row_checksum(conn, "items")
    assert len(h1) == 64
    conn.execute("INSERT INTO items VALUES (3);")
    h2 = verify_table_row_checksum(conn, "items")
    assert h1 != h2
    conn.close()
