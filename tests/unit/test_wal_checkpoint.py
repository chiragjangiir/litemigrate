import sqlite3
from litemigrate.wal_checkpoint import wal_checkpoint_truncate

def test_wal_checkpoint_truncate():
    conn = sqlite3.connect(":memory:")
    res = wal_checkpoint_truncate(conn)
    assert isinstance(res, dict)
    assert "busy" in res
    assert "log_pages" in res
    conn.close()
