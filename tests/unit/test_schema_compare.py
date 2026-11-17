import sqlite3
from litemigrate.schema_compare import compare_tables

def test_compare_tables():
    c1 = sqlite3.connect(":memory:")
    c2 = sqlite3.connect(":memory:")
    c1.execute("CREATE TABLE users (id INTEGER);")
    c2.execute("CREATE TABLE users (id INTEGER);")
    c2.execute("CREATE TABLE posts (id INTEGER);")
    diff = compare_tables(c1, c2)
    assert diff["added"] == ["posts"]
    assert diff["common"] == ["users"]
    assert diff["removed"] == []
