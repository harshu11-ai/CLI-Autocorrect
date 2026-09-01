import contextlib
import io
import unittest
from unittest.mock import patch, sentinel

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
    @patch("cli_autocorrect.cli.FrequencyCorrector", return_value=sentinel.corrector)
    def test_runs_supported_application(self, frequency_corrector, _which, run_in_pty) -> None:
        result = main(["codex", "--model", "example"])
        self.assertEqual(result, 7)
        frequency_corrector.assert_called_once_with(
            background=True,
            custom_corrections={},
        )
        run_in_pty.assert_called_once_with(
            ["codex", "--model", "example"],
            corrections=True,
            corrector=sentinel.corrector,
        )

    @patch("cli_autocorrect.cli.run_in_pty", return_value=0)
    @patch("cli_autocorrect.cli.shutil.which", return_value="/usr/local/bin/claude")
    def test_can_disable_corrections(self, _which, run_in_pty) -> None:
        result = main(["--no-corrections", "claude"])
        self.assertEqual(result, 0)
        run_in_pty.assert_called_once_with(
            ["claude"],
            corrections=False,
            corrector=None,
        )

    @patch("cli_autocorrect.cli.run_in_pty")
    @patch("cli_autocorrect.cli.shutil.which", return_value="/usr/local/bin/codex")
    def test_rejects_missing_explicit_config(self, _which, run_in_pty) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = main(["--config", "/does/not/exist.json", "codex"])
        self.assertEqual(result, 2)
        self.assertIn("configuration file does not exist", stderr.getvalue())
        run_in_pty.assert_not_called()

    @patch("cli_autocorrect.cli._run_doctor", return_value=0)
    def test_runs_doctor_without_application(self, run_doctor) -> None:
        self.assertEqual(main(["--doctor"]), 0)
        run_doctor.assert_called_once()


if __name__ == "__main__":
    unittest.main()
