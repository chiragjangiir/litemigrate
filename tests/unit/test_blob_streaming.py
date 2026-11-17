import sqlite3
from litemigrate.blob_streaming import read_blob_chunked

def test_read_blob():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE files (id INT, content BLOB);")
    raw = b"A" * 10000
    conn.execute("INSERT INTO files (id, content) VALUES (1, ?);", (raw,))
    chunks = list(read_blob_chunked(conn, "files", "content", 1, 4096))
    assert len(chunks) == 3
    assert b"".join(chunks) == raw
