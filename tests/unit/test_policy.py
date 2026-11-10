"""Unit tests for MigrationPolicy serialization, defaults, and allowlists."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from litemigrate.policy import MigrationPolicy


class TestPolicy(unittest.TestCase):
    def test_default_policy_is_strict(self) -> None:
        p = MigrationPolicy()
        self.assertEqual(len(p.allowed_dropped_tables), 0)
        self.assertEqual(len(p.allowed_row_loss_tables), 0)
        self.assertEqual(len(p.allowed_mutated_tables), 0)
        self.assertEqual(len(p.allowed_dropped_views), 0)
        self.assertEqual(len(p.allowed_dropped_triggers), 0)
        self.assertEqual(len(p.allowed_dropped_indexes), 0)
        self.assertTrue(p.disable_foreign_keys_during_migration)
        self.assertEqual(p.busy_timeout_ms, 3000)

    def test_json_file_roundtrip(self) -> None:
        p = MigrationPolicy(
            allowed_dropped_tables=frozenset(["temp_log"]),
            allowed_row_loss_tables=frozenset(["archive_events"]),
            allowed_mutated_tables=frozenset(["users"]),
            allowed_dropped_views=frozenset(["v_active"]),
            allowed_dropped_triggers=frozenset(["trg_audit"]),
            allowed_dropped_indexes=frozenset(["idx_email"]),
            disable_foreign_keys_during_migration=False,
            busy_timeout_ms=5000,
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "policy.json"
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(p.to_dict(), f)

            loaded = MigrationPolicy.from_file(path)
            self.assertEqual(loaded.allowed_dropped_tables, frozenset(["temp_log"]))
            self.assertEqual(loaded.allowed_row_loss_tables, frozenset(["archive_events"]))
            self.assertEqual(loaded.allowed_mutated_tables, frozenset(["users"]))
            self.assertEqual(loaded.allowed_dropped_views, frozenset(["v_active"]))
            self.assertEqual(loaded.allowed_dropped_triggers, frozenset(["trg_audit"]))
            self.assertEqual(loaded.allowed_dropped_indexes, frozenset(["idx_email"]))
            self.assertFalse(loaded.disable_foreign_keys_during_migration)
            self.assertEqual(loaded.busy_timeout_ms, 5000)


if __name__ == "__main__":
    unittest.main()
