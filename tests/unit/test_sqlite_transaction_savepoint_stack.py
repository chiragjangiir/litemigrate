import sqlite3
from litemigrate.sqlite_transaction_savepoint_stack import SqliteTransactionSavepointStack

def test_savepoint_stack():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (x INT)")
    stack = SqliteTransactionSavepointStack(conn)
    stack.push("sp1")
    conn.execute("INSERT INTO t VALUES (1)")
    stack.pop_commit()
    assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
