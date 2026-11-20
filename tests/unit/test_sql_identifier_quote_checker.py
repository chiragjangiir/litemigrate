from litemigrate.sql_identifier_quote_checker import SqlIdentifierQuoteChecker

def test_quote_checker():
    assert SqlIdentifierQuoteChecker.is_quoted('"users"') is True
    assert SqlIdentifierQuoteChecker.is_quoted('`users`') is True
    assert SqlIdentifierQuoteChecker.is_quoted('[users]') is True
    assert SqlIdentifierQuoteChecker.is_quoted('users') is False
