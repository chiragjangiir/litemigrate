import datetime

def format_migration_filename(description, timestamp=None):
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc)
    prefix = ts.strftime("%Y%m%d%H%M%S")
    clean_desc = "".join(c if c.isalnum() else "_" for c in description.lower()).strip("_")
    return f"{prefix}_{clean_desc}.sql"
