from litemigrate.migration_checksum_verifier import MigrationChecksumVerifier

def test_migration_checksum():
    content = "CREATE TABLE t (id INT);"
    import hashlib
    h = hashlib.sha256(content.encode()).hexdigest()
    assert MigrationChecksumVerifier.verify(content, h) is True
    assert MigrationChecksumVerifier.verify("altered", h) is False
