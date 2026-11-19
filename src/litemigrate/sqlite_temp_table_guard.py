import sqlite3
from contextlib import contextmanager

class SqliteTempTableGuard:
    @staticmethod
    @contextmanager
    def create_temp_table(conn: sqlite3.Connection, name: str, schema_ddl: str):
        conn.execute(f"CREATE TEMP TABLE {name} ({schema_ddl})")
        try:
            yield name
        finally:
            conn.execute(f"DROP TABLE IF EXISTS temp.{name}")
