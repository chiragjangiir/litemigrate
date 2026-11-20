import sqlite3
from litemigrate.in_memory_db_snapshot import InMemoryDbSnapshot

def test_snapshot_to_sql():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (x INT)")
    conn.execute("INSERT INTO t VALUES (10)")
    sql = InMemoryDbSnapshot.snapshot_to_sql(conn)
    assert "CREATE TABLE t" in sql
    assert "INSERT INTO" in sql
