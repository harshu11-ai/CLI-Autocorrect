import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli_autocorrect.config import ConfigurationError, default_config_path, load_configuration
from cli_autocorrect.corrector import ConservativeCorrector


class ConfigurationTests(unittest.TestCase):
    def test_uses_xdg_config_home(self) -> None:
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/example-config"}):
            self.assertEqual(
                default_config_path(),
                Path("/tmp/example-config/cli-autocorrect/config.json"),
            )

    def test_missing_default_configuration_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            configuration = load_configuration(Path(directory) / "missing.json")
        self.assertFalse(configuration.exists)
        self.assertEqual(configuration.corrections, {})

    def test_loads_personal_corrections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps({"corrections": {"awsome": "awesome"}}),
                encoding="utf-8",
            )
            configuration = load_configuration(path)

        self.assertTrue(configuration.exists)
        self.assertEqual(configuration.corrections, {"awsome": "awesome"})
        correction = ConservativeCorrector(configuration.corrections).suggest("awsome")
        self.assertIsNotNone(correction)
        assert correction is not None
        self.assertEqual(correction.replacement, "awesome")

    def test_reports_invalid_json_location(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"corrections": {', encoding="utf-8")
            with self.assertRaisesRegex(ConfigurationError, r"line 1, column"):
                load_configuration(path)

    def test_rejects_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text('{"language": "en"}', encoding="utf-8")
            with self.assertRaisesRegex(ConfigurationError, "unknown configuration key"):
                load_configuration(path)

    def test_rejects_unsafe_or_identity_corrections(self) -> None:
        invalid_mappings = (
            {"UseEffect": "useeffect"},
            {"src/file": "file"},
            {"same": "same"},
            {"typo": 42},
        )
        for mapping in invalid_mappings:
            with self.subTest(mapping=mapping), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "config.json"
                path.write_text(json.dumps({"corrections": mapping}), encoding="utf-8")
                with self.assertRaises(ConfigurationError):
                    load_configuration(path)


if __name__ == "__main__":
    unittest.main()
