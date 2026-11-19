from litemigrate.sql_keyword_escaper import SqlKeywordEscaper

def test_sql_keyword_escaper():
    assert SqlKeywordEscaper.escape_if_needed("order") == '"order"'
    assert SqlKeywordEscaper.escape_if_needed("table") == '"table"'
    assert SqlKeywordEscaper.escape_if_needed("normal_col") == "normal_col"
