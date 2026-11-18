import datetime
from litemigrate.migration_file_namer import format_migration_filename

def test_migration_filename():
    dt = datetime.datetime(2026, 11, 18, 12, 0, 0, tzinfo=datetime.timezone.utc)
    name = format_migration_filename("Add User Profile Index", timestamp=dt)
    assert name == "20261118120000_add_user_profile_index.sql"
