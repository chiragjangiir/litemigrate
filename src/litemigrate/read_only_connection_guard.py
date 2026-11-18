import sqlite3

def open_read_only_connection(db_path):
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True)
