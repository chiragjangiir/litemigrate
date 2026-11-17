import sqlite3
from litemigrate.checkpoint_monitor import get_wal_checkpoint_status

def test_checkpoint_status():
    conn = sqlite3.connect(":memory:")
    status = get_wal_checkpoint_status(conn)
    assert "busy" in status
