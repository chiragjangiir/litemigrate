from litemigrate.sqlite_statement_hasher import SqliteStatementHasher

def test_statement_hasher():
    h1 = SqliteStatementHasher.hash_statement("SELECT  *   FROM users;")
    h2 = SqliteStatementHasher.hash_statement("select * from users;")
    assert h1 == h2
    assert len(h1) == 64
