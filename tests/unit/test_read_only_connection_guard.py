import sqlite3
import tempfile
from litemigrate.read_only_connection_guard import open_read_only_connection

def test_read_only_guard():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        init_conn = sqlite3.connect(f.name)
        init_conn.execute("CREATE TABLE t (id INT);")
        init_conn.close()
        
        ro_conn = open_read_only_connection(f.name)
        assert ro_conn is not None
        ro_conn.close()
