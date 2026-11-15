import os
import unittest
from pathlib import Path
from litemigrate.config import LiteMigrateConfig


class TestLiteMigrateConfig(unittest.TestCase):
    def test_default_values(self):
        cfg = LiteMigrateConfig()
        self.assertEqual(cfg.timeout_seconds, 10.0)
        self.assertEqual(cfg.default_strategy, "auto")
        self.assertIsNone(cfg.backup_dir)
        self.assertTrue(cfg.enforce_foreign_keys)
        self.assertTrue(cfg.wal_mode_preferred)
        self.assertEqual(cfg.max_memory_mb, 64)

    def test_from_env_defaults(self):
        # Clear env overrides
        for k in ["LITEMIGRATE_TIMEOUT", "LITEMIGRATE_STRATEGY", "LITEMIGRATE_BACKUP_DIR"]:
            os.environ.pop(k, None)
        cfg = LiteMigrateConfig.from_env()
        self.assertEqual(cfg.timeout_seconds, 10.0)

    def test_from_env_overrides(self):
        os.environ["LITEMIGRATE_TIMEOUT"] = "25.5"
        os.environ["LITEMIGRATE_STRATEGY"] = "copy"
        os.environ["LITEMIGRATE_BACKUP_DIR"] = "/tmp/backups"
        try:
            cfg = LiteMigrateConfig.from_env()
            self.assertEqual(cfg.timeout_seconds, 25.5)
            self.assertEqual(cfg.default_strategy, "copy")
            self.assertEqual(cfg.backup_dir, Path("/tmp/backups"))
        finally:
            os.environ.pop("LITEMIGRATE_TIMEOUT", None)
            os.environ.pop("LITEMIGRATE_STRATEGY", None)
            os.environ.pop("LITEMIGRATE_BACKUP_DIR", None)


if __name__ == "__main__":
    unittest.main()
