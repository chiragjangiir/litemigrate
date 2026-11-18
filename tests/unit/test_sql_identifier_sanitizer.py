import pytest
from litemigrate.sql_identifier_sanitizer import quote_identifier

def test_quote_identifier():
    assert quote_identifier("users") == '"users"'
    assert quote_identifier('my "table"') == '"my ""table"""'
