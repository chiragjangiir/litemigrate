import sqlite3
from litemigrate.batch_exec import execute_script_with_progress

def test_execute_script_with_progress():
    conn = sqlite3.connect(":memory:")
    script = "CREATE TABLE a (v INT); INSERT INTO a VALUES (1); INSERT INTO a VALUES (2);"
    progress = []
    total = execute_script_with_progress(conn, script, lambda cur, tot: progress.append((cur, tot)))
    assert total == 3
    assert progress == [(1, 3), (2, 3), (3, 3)]
    conn.close()
