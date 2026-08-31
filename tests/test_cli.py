import contextlib
import io
import unittest
from unittest.mock import patch

from cli_autocorrect.cli import main


class CliTests(unittest.TestCase):
    def test_rejects_unsupported_application(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            main(["bash"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("supports only 'claude' and 'codex'", stderr.getvalue())

    @patch("cli_autocorrect.cli.run_in_pty", return_value=7)
    @patch("cli_autocorrect.cli.shutil.which", return_value="/usr/local/bin/codex")
    def test_runs_supported_application(self, _which, run_in_pty) -> None:
        result = main(["codex", "--model", "example"])
        self.assertEqual(result, 7)
        run_in_pty.assert_called_once_with(
            ["codex", "--model", "example"],
            corrections=True,
        )

    @patch("cli_autocorrect.cli.run_in_pty", return_value=0)
    @patch("cli_autocorrect.cli.shutil.which", return_value="/usr/local/bin/claude")
    def test_can_disable_corrections(self, _which, run_in_pty) -> None:
        result = main(["--no-corrections", "claude"])
        self.assertEqual(result, 0)
        run_in_pty.assert_called_once_with(["claude"], corrections=False)


if __name__ == "__main__":
    unittest.main()

