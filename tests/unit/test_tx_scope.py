import sqlite3
import pytest
from litemigrate.transaction_guard import transactional_migration_scope

def test_transactional_migration_scope_commit():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE counter (val INT);")
    with transactional_migration_scope(conn):
        conn.execute("INSERT INTO counter VALUES (42);")
    assert conn.execute("SELECT val FROM counter").fetchone()[0] == 42
    conn.close()

def test_transactional_migration_scope_rollback():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE counter (val INT);")
    with pytest.raises(ValueError):
        with transactional_migration_scope(conn):
            conn.execute("INSERT INTO counter VALUES (42);")
            raise ValueError("Failure")
    assert conn.execute("SELECT COUNT(*) FROM counter").fetchone()[0] == 0
    conn.close()
