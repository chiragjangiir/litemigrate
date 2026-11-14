"""Command-Line Interface (CLI) for LiteMigrate."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from litemigrate import __version__
from litemigrate.engine import LiteMigrateEngine
from litemigrate.exceptions import ConcurrencyConflictError, LockTimeoutError, SecurityError
from litemigrate.models import AuditReport, CloneStrategy, ValidationVerdict
from litemigrate.policy import MigrationPolicy


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="litemigrate",
        description="LiteMigrate — Safer SQLite migrations through shadow verification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  litemigrate inspect --db ./app.db
  litemigrate validate --db ./app.db --migration ./migrations/001_add_index.sql
  litemigrate apply --db ./app.db --migration ./migrations/001_add_index.sql --confirm
  litemigrate report --input ./audit-report.json

Safety Notes:
  • Local-first: Never uploads or transmits database contents.
  • Validation runs strictly against an isolated shadow copy; source is untouched.
  • Applying requires explicit confirmation and creates a pre-promotion backup.
  • Concurrency protection detects any concurrent source writes and prevents clobbering.
""",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"litemigrate {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. inspect
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect database schema, journal mode, and integrity.",
        description="Inspect database schema and integrity without displaying sensitive row contents.",
    )
    inspect_parser.add_argument(
        "--db",
        required=True,
        type=Path,
        help="Path to the SQLite database file to inspect.",
    )
    inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="Output inspection result in JSON format.",
    )

    # 2. validate
    val_parser = subparsers.add_parser(
        "validate",
        help="Test migration against an isolated shadow copy without modifying source.",
        description="Create a shadow database, execute migration, and audit safety invariants.",
    )
    val_parser.add_argument(
        "--db",
        required=True,
        type=Path,
        help="Path to the source SQLite database.",
    )
    val_parser.add_argument(
        "--migration",
        required=True,
        type=Path,
        help="Path to the SQL migration file.",
    )
    val_parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="Path to an optional JSON policy file declaring permitted drops/mutations.",
    )
    val_parser.add_argument(
        "--strategy",
        choices=[s.value for s in CloneStrategy],
        default=CloneStrategy.AUTO.value,
        help="Shadow cloning strategy (default: auto).",
    )
    val_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the JSON audit report to disk.",
    )
    val_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the audit report to stdout in JSON format.",
    )
    val_parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a condensed tabular summary of validation checks.",
    )

    # 3. apply
    apply_parser = subparsers.add_parser(
        "apply",
        help="Validate on shadow, verify source has not changed, and apply migration.",
        description="Validate migration on shadow database, require confirmation, and promote safely.",
    )
    apply_parser.add_argument(
        "--db",
        required=True,
        type=Path,
        help="Path to the source SQLite database.",
    )
    apply_parser.add_argument(
        "--migration",
        required=True,
        type=Path,
        help="Path to the SQL migration file.",
    )
    apply_parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="Path to an optional JSON policy file declaring permitted drops/mutations.",
    )
    apply_parser.add_argument(
        "--strategy",
        choices=[s.value for s in CloneStrategy],
        default=CloneStrategy.AUTO.value,
        help="Shadow cloning strategy (default: auto).",
    )
    apply_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicitly confirm migration promotion without interactive prompt.",
    )
    apply_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the JSON audit report to disk.",
    )
    apply_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the audit report to stdout in JSON format.",
    )

    # 4. report
    report_parser = subparsers.add_parser(
        "report",
        help="Display and summarize a previously generated audit report.",
        description="Format and display an existing JSON audit report.",
    )
    report_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input JSON audit report.",
    )
    report_parser.add_argument(
        "--json",
        action="store_true",
        help="Output the loaded audit report as normalized JSON.",
    )

    return parser


def handle_inspect(args: argparse.Namespace) -> int:
    try:
        report = LiteMigrateEngine.inspect(args.db)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 5
    except PermissionError as exc:
        print(f"Security Error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        return _report_cli_error(exc, "Error during inspection")

    if args.json:
        print(report.to_json())
        return 0

    print("═════════════════════════════════════════════════════════════════")
    print(" LiteMigrate — Database Inspection Report")
    print("═════════════════════════════════════════════════════════════════")
    print(f"  Database Path:         {report.path}")
    print(f"  SQLite Version:        {report.sqlite_version}")
    print(f"  Journal Mode:          {report.journal_mode}")
    print(f"  File Size:             {report.file_size_bytes:,} bytes")
    print(f"  Table Count:           {report.table_count}")
    print(f"  Schema Objects:        {report.schema_object_count}")
    print(f"  Foreign Keys Enabled:  {'Yes' if report.foreign_keys_enabled else 'No'}")
    print(f"  Database Integrity:    {'PASSED' if report.integrity_ok else 'FAILED'}")
    if not report.integrity_ok:
        print(f"  Integrity Details:     {report.integrity_message}")
    if report.tables:
        print("\n  User Tables:")
        for tbl in report.tables:
            print(f"    • {tbl}")
    print("═════════════════════════════════════════════════════════════════")
    return 0


# _report_cli_error prints an engine failure and returns the documented exit
# code (README "Exit Codes"): 3 for security, 2 for concurrency/lock, 5 otherwise.
def _report_cli_error(exc: Exception, prefix: str) -> int:
    if isinstance(exc, (PermissionError, SecurityError)):
        print(f"Security Error: {exc}", file=sys.stderr)
        return 3
    if isinstance(exc, (LockTimeoutError, ConcurrencyConflictError)):
        print(f"Concurrency Error: {exc}", file=sys.stderr)
        return 2
    print(f"{prefix}: {exc}", file=sys.stderr)
    return 5


def handle_validate(args: argparse.Namespace) -> int:
    policy = MigrationPolicy.from_file(args.policy) if args.policy else MigrationPolicy()
    strategy = CloneStrategy(args.strategy)

    try:
        report = LiteMigrateEngine.execute_and_validate(
            source_db=args.db,
            migration_sql=args.migration,
            policy=policy,
            clone_strategy=strategy,
            apply_to_source_on_pass=False,
            confirmed=False,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 5
    except PermissionError as exc:
        print(f"Security Error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        return _report_cli_error(exc, "Unexpected error")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report.to_json())

    if args.json:
        print(report.to_json())
    elif getattr(args, "summary", False):
        print("── LiteMigrate Execution Summary ──")
        print(f"  Verdict:       {report.verdict.value}")
        print(f"  Duration:      {report.total_elapsed_ms:.2f} ms")
        print(f"  FK Violations: {len(report.foreign_key_violations)}")
        print(f"  Integrity:     {'PASS' if report.integrity_check_passed else 'FAIL'}")
        print("───────────────────────────────────")
    else:
        _print_human_report(report, mode="VALIDATE")

    return _verdict_to_exit_code(report.verdict)


def handle_apply(args: argparse.Namespace) -> int:
    policy = MigrationPolicy.from_file(args.policy) if args.policy else MigrationPolicy()
    strategy = CloneStrategy(args.strategy)

    # Pre-flight check on confirmation
    confirmed = args.confirm
    if not confirmed:
        if sys.stdin.isatty():
            prompt = (
                f"Are you sure you want to validate and apply migration '{args.migration}' "
                f"to database '{args.db}'? [y/N]: "
            )
            response = input(prompt).strip().lower()
            if response in ("y", "yes"):
                confirmed = True
            else:
                print("Apply aborted by user.", file=sys.stderr)
                return 4
        else:
            print(
                "Error: Non-interactive environment detected. "
                "Applying a migration to source requires the --confirm flag.",
                file=sys.stderr,
            )
            return 4

    try:
        report = LiteMigrateEngine.execute_and_validate(
            source_db=args.db,
            migration_sql=args.migration,
            policy=policy,
            clone_strategy=strategy,
            apply_to_source_on_pass=True,
            confirmed=confirmed,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 5
    except PermissionError as exc:
        print(f"Security Error: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        return _report_cli_error(exc, "Unexpected error")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report.to_json())

    if args.json:
        print(report.to_json())
    else:
        _print_human_report(report, mode="APPLY")

    return _verdict_to_exit_code(report.verdict)


def handle_report(args: argparse.Namespace) -> int:
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            raw = f.read()
        report = AuditReport.from_json(raw)
    except Exception as exc:
        print(f"Error reading audit report: {exc}", file=sys.stderr)
        return 5

    if args.json:
        print(report.to_json())
    else:
        _print_human_report(report, mode="REPORT")

    return _verdict_to_exit_code(report.verdict)


def _verdict_to_exit_code(verdict: ValidationVerdict) -> int:
    if verdict == ValidationVerdict.PASSED:
        return 0
    if verdict in (
        ValidationVerdict.BLOCKED_SOURCE_MODIFIED_CONCURRENTLY,
        ValidationVerdict.BLOCKED_CONCURRENT_LOCK,
    ):
        return 2
    return 1


def _print_human_report(report: AuditReport, mode: str) -> None:
    print("═════════════════════════════════════════════════════════════════")
    print(f" LiteMigrate Audit Report — {mode}")
    print("═════════════════════════════════════════════════════════════════")
    print(f"  Verdict:               {report.verdict.value.upper()}")
    print(f"  Source Database:       {report.original_db_path}")
    print(f"  Promoted to Source:    {'Yes' if report.promoted_to_source else 'No'}")
    print(f"  Source DB Untouched:   {'Yes' if report.original_db_untouched else 'No'}")
    if report.backup_path:
        print(f"  Pre-Promote Backup:    {report.backup_path}")
    if report.clone_result:
        print(f"  Clone Strategy Used:   {report.clone_result.strategy_used.value}")
        print(f"  Clone Duration:        {report.clone_result.duration_ms:.2f} ms")
    print(f"  Migration Execution:   {report.migration_duration_ms:.2f} ms")
    print(f"  Audit Duration:        {report.audit_duration_ms:.2f} ms")
    print(f"  Total Elapsed Time:    {report.total_elapsed_ms:.2f} ms")

    if report.details:
        print("\n  Audit Findings & Details:")
        for d in report.details:
            print(f"    • {d}")

    if report.foreign_key_violations:
        print("\n  Foreign Key Violations:")
        for v in report.foreign_key_violations:
            print(f"    ✗ {v}")

    if report.dropped_tables:
        print(f"\n  Dropped Tables:        {', '.join(report.dropped_tables)}")
    if report.row_loss_tables:
        print(f"  Tables with Row Loss:  {', '.join(report.row_loss_tables)}")
    if report.mutated_tables:
        print(f"  Mutated Tables:        {', '.join(report.mutated_tables)}")
    if report.dropped_schema_objects:
        print(f"  Dropped Schema Objs:   {len(report.dropped_schema_objects)} objects")
        for obj in report.dropped_schema_objects:
            print(f"    • {obj.obj_type.upper()}: {obj.name} (on {obj.tbl_name})")

    print("═════════════════════════════════════════════════════════════════")


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return handle_inspect(args)
    if args.command == "validate":
        return handle_validate(args)
    if args.command == "apply":
        return handle_apply(args)
    if args.command == "report":
        return handle_report(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
