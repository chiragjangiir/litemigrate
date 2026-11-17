import sqlite3
from litemigrate.auto_vacuum import get_auto_vacuum_mode

def test_auto_vacuum_default():
    conn = sqlite3.connect(":memory:")
    mode = get_auto_vacuum_mode(conn)
    assert mode in ("NONE", "FULL", "INCREMENTAL")
