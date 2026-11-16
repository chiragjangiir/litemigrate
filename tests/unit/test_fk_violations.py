import sqlite3
from litemigrate.foreign_key_check import check_foreign_key_violations

def test_check_foreign_key_violations():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = OFF;")
    conn.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY);")
    conn.execute("CREATE TABLE child (id INT, p_id INT REFERENCES parent(id));")
    conn.execute("INSERT INTO child VALUES (1, 999);")
    violations = check_foreign_key_violations(conn, "child")
    assert len(violations) == 1
    assert violations[0]["table"] == "child"
    assert violations[0]["target"] == "parent"
    conn.close()
