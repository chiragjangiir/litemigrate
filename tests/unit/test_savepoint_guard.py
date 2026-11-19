import sqlite3
import pytest
from litemigrate.savepoint_guard import SavepointGuard

def test_savepoint_success_and_rollback():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (x INT)")
    with SavepointGuard.guard(conn, "sp1"):
        conn.execute("INSERT INTO t VALUES (1)")
    cur = conn.cursor()
    assert cur.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1

    with pytest.raises(ValueError):
        with SavepointGuard.guard(conn, "sp2"):
            conn.execute("INSERT INTO t VALUES (2)")
            raise ValueError("abort")
    assert cur.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
