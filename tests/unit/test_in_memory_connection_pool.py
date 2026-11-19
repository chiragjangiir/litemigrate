from litemigrate.in_memory_connection_pool import InMemoryConnectionPool

def test_shared_memory_pool():
    pool = InMemoryConnectionPool()
    c1 = pool.get_shared_memory_connection("test_db")
    c1.execute("CREATE TABLE t (id INT)")
    c1.execute("INSERT INTO t VALUES (42)")
    c1.commit()

    c2 = pool.get_shared_memory_connection("test_db")
    assert c2.execute("SELECT id FROM t").fetchone()[0] == 42
