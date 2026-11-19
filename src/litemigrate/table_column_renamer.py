class TableColumnRenamer:
    @staticmethod
    def generate_rename_sql(table_name: str, old_column: str, new_column: str) -> str:
        return f'ALTER TABLE "{table_name}" RENAME COLUMN "{old_column}" TO "{new_column}";'
