"""Pseudo-terminal wrapper used to run an interactive child application."""

from __future__ import annotations

import errno
import fcntl
import os
import pty
import select
import signal
import sys
import termios
import tty
from collections.abc import Sequence
from contextlib import suppress

from cli_autocorrect.input_processor import InputProcessor


class TerminalRequiredError(RuntimeError):
    """Raised when the proxy is invoked without an interactive terminal."""


def run_in_pty(command: Sequence[str], *, corrections: bool = True) -> int:
    """Run *command* in a child PTY and proxy the current terminal to it."""
    if not command:
        raise ValueError("command cannot be empty")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise TerminalRequiredError("stdin and stdout must both be interactive terminals")

    child_pid, master_fd = pty.fork()
    if child_pid == 0:
        try:
            os.execvp(command[0], list(command))
        except OSError as error:
            print(f"cli-autocorrect: unable to launch {command[0]}: {error}", file=sys.stderr)
            os._exit(127)

    stdin_fd = sys.stdin.fileno()
    stdout_fd = sys.stdout.fileno()
    original_attributes = termios.tcgetattr(stdin_fd)
    old_winch_handler = signal.getsignal(signal.SIGWINCH)
    old_term_handler = signal.getsignal(signal.SIGTERM)
    processor = InputProcessor() if corrections else None

    def copy_window_size(*_: object) -> None:
        try:
            size = fcntl.ioctl(stdout_fd, termios.TIOCGWINSZ, b"\0" * 8)
            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, size)
            os.kill(child_pid, signal.SIGWINCH)
        except OSError:
            pass

    def forward_termination(signum: int, _frame: object) -> None:
        with suppress(ProcessLookupError):
            os.kill(child_pid, signum)

    try:
        tty.setraw(stdin_fd)
        signal.signal(signal.SIGWINCH, copy_window_size)
        signal.signal(signal.SIGTERM, forward_termination)
        copy_window_size()

        while True:
            readable, _, _ = select.select([stdin_fd, master_fd], [], [])
            if master_fd in readable:
                try:
                    child_output = os.read(master_fd, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        break
                    raise
                if not child_output:
                    break
                _write_all(stdout_fd, child_output)

            if stdin_fd in readable:
                user_input = os.read(stdin_fd, 4096)
                if not user_input:
                    break
                child_input = processor.feed(user_input) if processor else user_input
                _write_all(master_fd, child_input)
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, original_attributes)
        signal.signal(signal.SIGWINCH, old_winch_handler)
        signal.signal(signal.SIGTERM, old_term_handler)
        with suppress(OSError):
            os.close(master_fd)

    _, status = os.waitpid(child_pid, 0)
    return os.waitstatus_to_exitcode(status)


def _write_all(file_descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(file_descriptor, view)
        view = view[written:]
