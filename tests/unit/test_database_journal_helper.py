import sqlite3
from litemigrate.database_journal_helper import get_journal_mode

def test_get_journal_mode():
    conn = sqlite3.connect(":memory:")
    mode = get_journal_mode(conn)
    assert mode in ("MEMORY", "DELETE", "WAL", "OFF")
