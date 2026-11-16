import sqlite3
from litemigrate.query_plan import explain_query_plan

def test_explain_query_plan():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT);")
    plan = explain_query_plan(conn, "SELECT * FROM users WHERE id = 1")
    assert len(plan) >= 1
    assert any("SEARCH" in p["detail"] or "SCAN" in p["detail"] for p in plan)
    conn.close()
