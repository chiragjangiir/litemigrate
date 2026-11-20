from litemigrate.sqlite_vacuum_into_runner import SqliteVacuumIntoRunner

def test_vacuum_into_runner():
    sql = SqliteVacuumIntoRunner.build_vacuum_into_sql("/tmp/backup.db")
    assert sql == "VACUUM INTO '/tmp/backup.db';"
