import sqlite3
from litemigrate.schema_migration_lock import SchemaMigrationLock

def test_migration_lock():
    conn = sqlite3.connect(":memory:")
    assert SchemaMigrationLock.acquire(conn, "proc-1") is True
    assert SchemaMigrationLock.acquire(conn, "proc-2") is False
    SchemaMigrationLock.release(conn)
    assert SchemaMigrationLock.acquire(conn, "proc-2") is True
