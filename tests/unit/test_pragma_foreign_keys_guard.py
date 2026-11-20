import sqlite3
from litemigrate.pragma_foreign_keys_guard import PragmaForeignKeysGuard

def test_foreign_keys_guard():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    with PragmaForeignKeysGuard.disabled(conn):
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 0
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
