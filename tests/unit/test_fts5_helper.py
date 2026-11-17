from litemigrate.fts5_helper import generate_fts5_ddl

def test_generate_fts5_ddl():
    sql = generate_fts5_ddl("articles_fts", ["title", "content"])
    assert sql == "CREATE VIRTUAL TABLE articles_fts USING fts5(title, content);"
