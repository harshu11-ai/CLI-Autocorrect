"""Command-line entry point."""

from __future__ import annotations

import argparse
import shutil
import sys

from cli_autocorrect import __version__
from cli_autocorrect.pty_proxy import TerminalRequiredError, run_in_pty

SUPPORTED_APPS = {"claude", "codex"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli-autocorrect",
        description="Run Claude Code or Codex with conservative local autocorrect.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--no-corrections",
        action="store_true",
        help="run as a transparent PTY proxy without changing input",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="claude or codex, followed by any arguments for that application",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    command = list(arguments.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        parser.error("provide either 'claude' or 'codex' to run")

    application = command[0]
    if application not in SUPPORTED_APPS:
        parser.error("the prototype currently supports only 'claude' and 'codex'")
    if shutil.which(application) is None:
        parser.error(f"could not find '{application}' on PATH")

    try:
        return run_in_pty(command, corrections=not arguments.no_corrections)
    except TerminalRequiredError as error:
        print(f"cli-autocorrect: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

