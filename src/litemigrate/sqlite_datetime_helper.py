import datetime

def to_sqlite_timestamp(dt):
    if dt.tzinfo is not None:
        dt = dt.astimezone(datetime.timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
