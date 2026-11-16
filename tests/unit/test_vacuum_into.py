import sqlite3
from litemigrate.vacuum_into import safe_vacuum_into

def test_safe_vacuum_into(tmp_path):
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (v TEXT);")
    conn.execute("INSERT INTO test VALUES ('ok');")
    dest = tmp_path / "backup.sqlite3"
    assert safe_vacuum_into(conn, str(dest)) is True
    assert dest.exists()
    conn.close()
