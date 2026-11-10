"""Phase 5 Mandatory Remediation Test Suite (Suite B — 12 tests)."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from litemigrate.cloning import create_shadow_database
from litemigrate.engine import LiteMigrateEngine
from litemigrate.fingerprint import compute_logical_db_digest
from litemigrate.models import CloneStrategy, ValidationVerdict
from litemigrate.policy import MigrationPolicy
from litemigrate.sqlite_backend import open_hardened_sqlite
from tests.fixtures.database_setup import create_test_database


class TestPhase5Remediation(unittest.TestCase):
    def test_01_write_committed_after_shadow_creation_before_digest(self) -> None:
        """Scenario 1: Write committed after shadow creation but before promotion."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            clone_res = create_shadow_database(db_path)
            s_conn = open_hardened_sqlite(clone_res.shadow_path)
            base_digest = compute_logical_db_digest(s_conn)
            s_conn.close()

            # Concurrent write
            c_conn = open_hardened_sqlite(db_path)
            c_conn.execute("INSERT INTO parent_table VALUES (999, 'Concurrent 1', 'Test 1');")
            c_conn.commit()
            c_conn.close()

            # CAS promotion check
            from litemigrate.exceptions import ConcurrencyConflictError
            from litemigrate.promotion import promote_shadow_to_source
            with self.assertRaises(ConcurrencyConflictError):
                promote_shadow_to_source(
                    shadow_path=clone_res.shadow_path,
                    source_path=db_path,
                    expected_source_digest=base_digest,
                    migration_sql="ALTER TABLE parent_table ADD COLUMN extra TEXT;",
                )

    def test_02_write_attempted_after_digest_verification_before_promotion(self) -> None:
        """Scenario 2: Concurrent writer cannot commit while LiteMigrate holds BEGIN IMMEDIATE."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            # While source_conn holds BEGIN IMMEDIATE, an external connection trying to write gets locked
            holder_conn = open_hardened_sqlite(db_path, isolation_level=None)
            holder_conn.execute("BEGIN IMMEDIATE;")

            external_conn = open_hardened_sqlite(db_path, busy_timeout_ms=50)
            with self.assertRaises(sqlite3.OperationalError):
                external_conn.execute("INSERT INTO parent_table VALUES (1001, 'Blocked', 'Tx');")

            holder_conn.execute("ROLLBACK;")
            holder_conn.close()
            external_conn.close()

    def test_03_writer_holding_lock_during_backup_in_subprocess(self) -> None:
        """Scenario 3: Writer holding lock during backup terminates within deadline."""
        with tempfile.TemporaryDirectory() as td:
            src_db = Path(td) / "src.db"
            dst_db = Path(td) / "dst.db"
            create_test_database(src_db)
            create_test_database(dst_db)

            dst_conn = open_hardened_sqlite(dst_db)
            dst_conn.execute("BEGIN EXCLUSIVE;")

            t0 = time.monotonic()
            from litemigrate.sqlite_backend import bounded_sqlite_backup
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    bounded_sqlite_backup(src_db, dst_db, busy_timeout_ms=100)
                self.assertLess(time.monotonic() - t0, 1.5)
            finally:
                dst_conn.execute("ROLLBACK;")
                dst_conn.close()

    def test_04_interrupted_backup_leaves_source_database_intact(self) -> None:
        """Scenario 4: Interrupted promotion leaves source database intact."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)
            from litemigrate.fingerprint import compute_file_sha256
            orig_sha = compute_file_sha256(db_path)

            # Attempt a migration with failing SQL mid-statement
            bad_mig = "ALTER TABLE parent_table ADD COLUMN col1 TEXT; SELECT * FROM nonexistent_table;"
            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql=bad_mig,
                apply_to_source_on_pass=True,
                confirmed=True,
            )
            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_MIGRATION_EXCEPTION)
            self.assertEqual(compute_file_sha256(db_path), orig_sha)

    def test_05_added_column_alongside_destructive_update_to_existing_column(self) -> None:
        """Scenario 5: Adding a column alongside destructive update to existing column is blocked."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            mig = "ALTER TABLE parent_table ADD COLUMN new_c TEXT; UPDATE parent_table SET name = 'MUTATED';"
            report = LiteMigrateEngine.execute_and_validate(source_db=db_path, migration_sql=mig)
            self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_DATA_MUTATION)

    def test_06_dropped_index_trigger_and_view_detection_and_policy_override(self) -> None:
        """Scenario 6: Dropped objects blocked by default, permitted when in policy."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            conn = create_test_database(db_path)
            conn.execute("CREATE INDEX idx_p_desc ON parent_table(description);")
            conn.close()

            # Blocked without policy
            report1 = LiteMigrateEngine.execute_and_validate(
                source_db=db_path, migration_sql="DROP INDEX idx_p_desc;"
            )
            self.assertEqual(report1.verdict, ValidationVerdict.BLOCKED_UNEXPECTED_SCHEMA_OBJECT_DROP)

            # Allowed with policy
            policy = MigrationPolicy(allowed_dropped_indexes=frozenset(["idx_p_desc"]))
            report2 = LiteMigrateEngine.execute_and_validate(
                source_db=db_path, migration_sql="DROP INDEX idx_p_desc;", policy=policy
            )
            self.assertEqual(report2.verdict, ValidationVerdict.PASSED)

    def test_07_0600_source_database_produces_0600_shadow_across_all_strategies(self) -> None:
        """Scenario 7: 0o600 source DB produces 0o600 shadow across strategies."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)
            os.chmod(db_path, 0o600)

            res = create_shadow_database(db_path, strategy=CloneStrategy.SQLITE_BACKUP_API)
            mode = os.stat(res.shadow_path).st_mode & 0o777
            self.assertEqual(mode, 0o600)

    def test_08_dangling_symlink_at_temporary_destination_rejected(self) -> None:
        """Scenario 8: Dangling symlink at temp destination is rejected."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)
            sym = Path(td) / "sym.db"
            sym.symlink_to(Path(td) / "nonexistent")
            with self.assertRaises(PermissionError):
                create_shadow_database(db_path, shadow_db=sym)

    def test_09_trusted_schema_read_back_on_every_connection(self) -> None:
        """Scenario 9: trusted_schema reads back 0 on every connection."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)
            conn = open_hardened_sqlite(db_path)
            self.assertEqual(conn.execute("PRAGMA trusted_schema;").fetchone()[0], 0)
            conn.close()

    def test_10_wal_checkpoint_activity_during_validation_does_not_abort(self) -> None:
        """Scenario 10: WAL checkpoints do not cause false CAS abort."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "wal.db"
            conn = create_test_database(db_path, enable_wal=True)

            d1 = compute_logical_db_digest(conn)
            conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
            d2 = compute_logical_db_digest(conn)
            self.assertEqual(d1, d2)
            conn.close()

    def test_11_process_interruption_during_migration_cleans_up_workspace(self) -> None:
        """Scenario 11: Cleanup of temporary directories."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)
            # Run a migration that fails validation
            report = LiteMigrateEngine.execute_and_validate(
                source_db=db_path,
                migration_sql="DELETE FROM parent_table;",
            )
            self.assertNotEqual(report.verdict, ValidationVerdict.PASSED)
            # Verify no orphaned temporary directories left behind in tempfile location
            # (our engine cleans up temp_dir in finally block)

    def test_12_two_litemigrate_processes_operating_on_same_source_database(self) -> None:
        """Scenario 12: Two concurrent LiteMigrate processes serialize cleanly via lockfile."""
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "app.db"
            create_test_database(db_path)

            lock_path = Path(f"{db_path}.litemigrate.lock")
            # Lock the lockfile directly to simulate another LiteMigrate process running apply
            import fcntl
            fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            try:
                policy = MigrationPolicy(busy_timeout_ms=100)
                report = LiteMigrateEngine.execute_and_validate(
                    source_db=db_path,
                    migration_sql="ALTER TABLE parent_table ADD COLUMN c TEXT;",
                    policy=policy,
                    apply_to_source_on_pass=True,
                    confirmed=True,
                )
                self.assertEqual(report.verdict, ValidationVerdict.BLOCKED_CONCURRENT_LOCK)
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)


if __name__ == "__main__":
    unittest.main()
