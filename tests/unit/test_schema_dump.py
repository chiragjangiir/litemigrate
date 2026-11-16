import sqlite3
from litemigrate.schema_dump import dump_schema_sql_normalized

def test_dump_schema_sql_normalized():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY);")
    conn.execute("CREATE INDEX idx_users_id ON users(id);")
    schema = dump_schema_sql_normalized(conn)
    assert "CREATE TABLE users" in schema
    assert "CREATE INDEX idx_users_id" in schema
    conn.close()
