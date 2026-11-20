from litemigrate.sql_string_literal_escaper import SqlStringLiteralEscaper

def test_literal_escaper():
    assert SqlStringLiteralEscaper.escape_literal("O'Reilly") == "'O''Reilly'"
    assert SqlStringLiteralEscaper.escape_literal(None) == "NULL"
