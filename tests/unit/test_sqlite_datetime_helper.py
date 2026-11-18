import datetime
from litemigrate.sqlite_datetime_helper import to_sqlite_timestamp

def test_sqlite_timestamp():
    dt = datetime.datetime(2026, 11, 18, 15, 30, 45, tzinfo=datetime.timezone.utc)
    assert to_sqlite_timestamp(dt) == "2026-11-18 15:30:45"
