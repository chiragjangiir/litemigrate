import sqlite3
from litemigrate.in_memory_clone_helper import clone_to_memory

def test_clone_to_memory():
    src = sqlite3.connect(":memory:")
    src.execute("CREATE TABLE t (v INT);")
    src.execute("INSERT INTO t VALUES (42);")
    dest = clone_to_memory(src)
    cursor = dest.execute("SELECT v FROM t;")
    assert cursor.fetchone()[0] == 42
