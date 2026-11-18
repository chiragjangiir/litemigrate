from litemigrate.sql_comment_stripper import strip_sql_comments

def test_strip_comments():
    sql = """
    -- initial schema
    SELECT * /* all columns */ FROM users;
    """
    clean = strip_sql_comments(sql)
    assert "-- initial schema" not in clean
    assert "/* all columns */" not in clean
    assert "SELECT *  FROM users;" in clean
