from litemigrate.temp_table import generate_temp_table_migration_sql

def test_generate_temp_table_migration_sql():
    sql = generate_temp_table_migration_sql("orders", ["id", "user_id", "total"])
    assert 'ALTER TABLE "orders" RENAME TO "orders__old_backup";' in sql
    assert 'INSERT INTO "orders" ("id", "user_id", "total") SELECT "id", "user_id", "total" FROM "orders__old_backup";' in sql
    assert 'DROP TABLE "orders__old_backup";' in sql
