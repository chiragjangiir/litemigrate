import sqlite3
import pytest
from litemigrate.savepoint_manager import nested_savepoint

def test_nested_savepoint_rollback():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE log (step TEXT);")
    conn.execute("INSERT INTO log VALUES ('step1');")
    with pytest.raises(RuntimeError):
        with nested_savepoint(conn, "sp1"):
            conn.execute("INSERT INTO log VALUES ('step2');")
            raise RuntimeError("inner error")
    rows = conn.execute("SELECT step FROM log").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "step1"
    conn.close()
