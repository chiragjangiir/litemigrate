import sqlite3
from litemigrate.sqlite_vacuum_analyzer import SqliteVacuumAnalyzer

def test_should_vacuum():
    conn = sqlite3.connect(":memory:")
    assert SqliteVacuumAnalyzer.should_vacuum(conn) is False
