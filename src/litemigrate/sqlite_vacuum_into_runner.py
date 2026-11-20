import os

class SqliteVacuumIntoRunner:
    @staticmethod
    def build_vacuum_into_sql(destination_path: str) -> str:
        if not destination_path:
            raise ValueError("Destination path required")
        escaped = destination_path.replace("'", "''")
        return f"VACUUM INTO '{escaped}';"
