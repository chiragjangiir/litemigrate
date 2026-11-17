import sqlite3
from litemigrate.migration_history import init_history_table, record_migration

def test_history_table():
    conn = sqlite3.connect(":memory:")
    assert init_history_table(conn) is True
    record_migration(conn, "001_init", "abc123sha")
    cursor = conn.execute("SELECT count(*) FROM _litemigrate_history;")
    assert cursor.fetchone()[0] == 1
