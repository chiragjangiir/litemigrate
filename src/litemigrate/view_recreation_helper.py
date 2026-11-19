import sqlite3
from typing import List, Tuple

class ViewRecreationHelper:
    @staticmethod
    def extract_views(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
        cur = conn.cursor()
        cur.execute("SELECT name, sql FROM sqlite_master WHERE type='view' AND sql IS NOT NULL")
        return cur.fetchall()

    @staticmethod
    def drop_views(conn: sqlite3.Connection, views: List[Tuple[str, str]]):
        for name, _ in views:
            conn.execute(f'DROP VIEW IF EXISTS "{name}"')

    @staticmethod
    def restore_views(conn: sqlite3.Connection, views: List[Tuple[str, str]]):
        for _, sql in views:
            conn.execute(sql)
