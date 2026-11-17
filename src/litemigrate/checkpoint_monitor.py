def get_wal_checkpoint_status(conn):
    try:
        cursor = conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
        row = cursor.fetchone()
        return {"busy": row[0], "log": row[1], "checkpointed": row[2]}
    except Exception:
        return {"busy": 0, "log": 0, "checkpointed": 0}
