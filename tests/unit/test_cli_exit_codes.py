"""CLI failures must use the documented exit codes (README, "Exit Codes")."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr
from unittest import mock

from litemigrate import cli
from litemigrate.exceptions import ConcurrencyConflictError, LockTimeoutError, SecurityError


class TestCliEngineErrorCodes(unittest.TestCase):
    def _validate_with(self, exc: Exception) -> tuple[int, str]:
        argv = ["validate", "--db", "app.db", "--migration", "m.sql"]
        stderr = io.StringIO()
        with mock.patch.object(cli.LiteMigrateEngine, "execute_and_validate", side_effect=exc):
            with redirect_stderr(stderr):
                code = cli.main(argv)
        return code, stderr.getvalue()

    def test_security_error_exits_3(self) -> None:
        code, err = self._validate_with(SecurityError("refusing symlinked database"))
        self.assertEqual(code, 3)
        self.assertIn("Security Error: refusing symlinked database", err)

    def test_lock_timeout_exits_2(self) -> None:
        code, err = self._validate_with(LockTimeoutError("lock not acquired"))
        self.assertEqual(code, 2)
        self.assertIn("Concurrency Error: lock not acquired", err)

    def test_concurrency_conflict_exits_2(self) -> None:
        code, err = self._validate_with(ConcurrencyConflictError("source changed"))
        self.assertEqual(code, 2)
        self.assertIn("Concurrency Error: source changed", err)

    def test_execution_failure_still_exits_5(self) -> None:
        code, err = self._validate_with(RuntimeError("disk full"))
        self.assertEqual(code, 5)
        self.assertIn("Unexpected error: disk full", err)


if __name__ == "__main__":
    unittest.main()
