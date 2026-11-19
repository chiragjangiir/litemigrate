from litemigrate.table_column_renamer import TableColumnRenamer

def test_generate_rename_sql():
    sql = TableColumnRenamer.generate_rename_sql("users", "email_addr", "email")
    assert sql == 'ALTER TABLE "users" RENAME COLUMN "email_addr" TO "email";'
