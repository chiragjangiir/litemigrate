import argparse
import sys

def main(argv=None):
    parser = argparse.ArgumentParser(prog="litemigrate", description="Lightweight SQLite Migration Tool")
    parser.add_argument("--version", action="version", version="litemigrate 0.1.0")
    parser.add_argument("command", choices=["status", "migrate", "verify"], nargs="?", default="status")
    args = parser.parse_args(argv)
    print(f"litemigrate running command: {args.command}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
