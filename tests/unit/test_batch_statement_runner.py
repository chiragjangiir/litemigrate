import sqlite3
from litemigrate.batch_statement_runner import BatchStatementRunner

def test_batch_statement_runner():
    conn = sqlite3.connect(":memory:")
    stmts = ["CREATE TABLE a (id INT);", "INSERT INTO a VALUES (1);", "INSERT INTO a VALUES (2);"]
    executed = BatchStatementRunner.execute_script(conn, stmts)
    assert executed == 3
    assert conn.execute("SELECT COUNT(*) FROM a").fetchone()[0] == 2
