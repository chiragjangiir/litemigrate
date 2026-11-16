import sqlite3
import time
from litemigrate.engine import execute_script_with_progress

def test_migration_benchmark():
    conn = sqlite3.connect(":memory:")
    sql = """
    CREATE TABLE benchmark_users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL
    );
    INSERT INTO benchmark_users (username, email) VALUES ('user1', 'user1@example.com');
    """
    start = time.perf_counter()
    count = execute_script_with_progress(conn, sql)
    elapsed = time.perf_counter() - start
    assert count == 2
    assert elapsed < 0.1
