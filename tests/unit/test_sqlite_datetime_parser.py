from litemigrate.sqlite_datetime_parser import SqliteDatetimeParser

def test_parse_to_epoch():
    epoch = SqliteDatetimeParser.parse_to_epoch("2026-11-19 12:00:00Z")
    assert epoch is not None
    assert SqliteDatetimeParser.parse_to_epoch("invalid-date") is None
