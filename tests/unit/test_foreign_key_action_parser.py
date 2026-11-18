import sqlite3
from litemigrate.foreign_key_action_parser import get_foreign_key_rules

def test_foreign_key_rules():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE parent (id INT PRIMARY KEY);")
    conn.execute("CREATE TABLE child (id INT, p_id INT REFERENCES parent(id) ON DELETE CASCADE);")
    rules = get_foreign_key_rules(conn, "child")
    assert len(rules) == 1
    assert rules[0]["on_delete"] == "CASCADE"
