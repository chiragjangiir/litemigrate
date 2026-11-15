import unittest
from litemigrate.diff import SchemaDiff


class TestSchemaDiff(unittest.TestCase):
    def test_detects_added_and_dropped_tables(self):
        before = ["users", "orders", "legacy_logs"]
        after = ["users", "orders", "audit_events", "payments"]

        diff = SchemaDiff.compute(before, after)
        self.assertEqual(diff.added_tables, ("audit_events", "payments"))
        self.assertEqual(diff.dropped_tables, ("legacy_logs",))
        self.assertEqual(diff.common_tables, ("orders", "users"))

    def test_identical_schemas_have_empty_diffs(self):
        tables = ["users", "accounts"]
        diff = SchemaDiff.compute(tables, tables)
        self.assertEqual(diff.added_tables, ())
        self.assertEqual(diff.dropped_tables, ())
        self.assertEqual(diff.common_tables, ("accounts", "users"))


if __name__ == "__main__":
    unittest.main()
