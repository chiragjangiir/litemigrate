import sqlite3
from litemigrate.table_row_comparator import TableRowComparator

def test_table_row_comparator():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t1 (id INT)")
    conn.execute("CREATE TABLE t2 (id INT)")
    conn.execute("INSERT INTO t1 VALUES (1), (2)")
    conn.execute("INSERT INTO t2 VALUES (1), (2)")
    a, b, matches = TableRowComparator.compare_counts(conn, "t1", "t2")
    assert matches is True
