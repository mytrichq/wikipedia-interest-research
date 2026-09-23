"""Command-line entry point.

Contract for agents: results go to stdout (compact, machine-readable), diagnostics to
stderr, and every failure exits non-zero with a message that says what to do next.
"""

from __future__ import annotations

import argparse
import sys

from wir import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wir",
        description=(
            "Wikipedia Interest Research: measure how interest in a topic changes "
            "across Wikipedia language editions, judge how trustworthy the trend is, "
            "and produce a one-page PDF report."
        ),
    )
    parser.add_argument("--version", action="version", version=f"wir {__version__}")
    parser.add_subparsers(dest="command", metavar="<command>")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
