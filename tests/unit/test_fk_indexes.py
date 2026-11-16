import sqlite3
from litemigrate.index_diff import detect_missing_indexes_for_foreign_keys

def test_detect_missing_indexes():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY);")
    conn.execute("CREATE TABLE books (id INTEGER PRIMARY KEY, author_id INTEGER REFERENCES authors(id));")
    missing = detect_missing_indexes_for_foreign_keys(conn, "books")
    assert len(missing) == 1
    assert missing[0]["column"] == "author_id"
    
    conn.execute("CREATE INDEX idx_books_author ON books(author_id);")
    assert len(detect_missing_indexes_for_foreign_keys(conn, "books")) == 0
    conn.close()
