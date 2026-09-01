"""Command-line entry point."""

from __future__ import annotations

import argparse
import platform
import shutil
import sys

from cli_autocorrect import __version__
from cli_autocorrect.config import ConfigurationError, UserConfiguration, load_configuration
from cli_autocorrect.corrector import FrequencyCorrector
from cli_autocorrect.pty_proxy import TerminalRequiredError, run_in_pty

SUPPORTED_APPS = {"claude", "codex"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli-autocorrect",
        description="Run Claude Code or Codex with local autocorrect and text expansion.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--no-corrections",
        action="store_true",
        help="run as a transparent PTY proxy without changing input",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="load personal corrections and abbreviations from PATH",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="check the local installation and exit",
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
    if arguments.doctor:
        if command:
            parser.error("--doctor cannot be combined with an application command")
        configuration = _load_configuration(arguments.config)
        if configuration is None:
            return 2
        return _run_doctor(configuration)

    if not command:
        parser.error("provide either 'claude' or 'codex' to run")

    application = command[0]
    if application not in SUPPORTED_APPS:
        parser.error("the prototype currently supports only 'claude' and 'codex'")
    if shutil.which(application) is None:
        parser.error(f"could not find '{application}' on PATH")

    corrector = None
    if not arguments.no_corrections:
        configuration = _load_configuration(arguments.config)
        if configuration is None:
            return 2
        corrector = FrequencyCorrector(
            background=True,
            custom_corrections=configuration.corrections,
            abbreviations=configuration.abbreviations,
        )

    try:
        return run_in_pty(
            command,
            corrections=not arguments.no_corrections,
            corrector=corrector,
        )
    except TerminalRequiredError as error:
        print(f"cli-autocorrect: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"cli-autocorrect: terminal I/O failed: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


def _load_configuration(path: str | None) -> UserConfiguration | None:
    try:
        configuration = load_configuration(path)
        if path is not None and not configuration.exists:
            raise ConfigurationError(f"configuration file does not exist: {configuration.path}")
        return configuration
    except ConfigurationError as error:
        print(f"cli-autocorrect: {error}", file=sys.stderr)
        return None


def _run_doctor(configuration: UserConfiguration) -> int:
    corrector = FrequencyCorrector(
        background=False,
        custom_corrections=configuration.corrections,
        abbreviations=configuration.abbreviations,
    )
    dictionary_ready = corrector.wait_until_ready(0)
    config_status = "not created (using built-in defaults)"
    if configuration.exists:
        config_status = (
            f"loaded ({len(configuration.corrections)} personal corrections, "
            f"{len(configuration.abbreviations)} abbreviations)"
        )

    print(f"CLI Autocorrect: {__version__}")
    print(f"Python: {platform.python_version()}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Config: {configuration.path} — {config_status}")
    print(f"Dictionary: {'ready' if dictionary_ready else 'failed'}")
    for application in sorted(SUPPORTED_APPS):
        executable = shutil.which(application)
        print(f"{application}: {executable or 'not found'}")
    terminal_status = (
        "interactive" if sys.stdin.isatty() and sys.stdout.isatty() else "not interactive"
    )
    print(f"Terminal: {terminal_status}")

    if corrector.load_error is not None:
        print(f"Dictionary error: {corrector.load_error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
