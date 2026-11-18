import sqlite3

def clone_to_memory(source_conn):
    dest = sqlite3.connect(":memory:")
    for line in source_conn.iterdump():
        dest.execute(line)
    return dest
