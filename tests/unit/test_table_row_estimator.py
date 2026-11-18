import sqlite3
from litemigrate.table_row_estimator import estimate_table_rows

def test_estimate_rows():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    conn.execute("INSERT INTO users VALUES (1, 'alice'), (2, 'bob');")
    assert estimate_table_rows(conn, "users") == 2
