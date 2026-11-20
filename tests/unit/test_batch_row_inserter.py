import sqlite3
from litemigrate.batch_row_inserter import BatchRowInserter

def test_batch_inserter():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (id INT)")
    rows = [(i,) for i in range(25)]
    inserted = BatchRowInserter.insert_in_batches(conn, "INSERT INTO t VALUES (?)", rows, batch_size=10)
    assert inserted == 25
    assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 25
