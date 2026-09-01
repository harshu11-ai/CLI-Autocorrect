"""Validated user configuration for CLI Autocorrect."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

_PLAIN_WORD = re.compile(r"^[a-z]+$")
_MAX_WORD_LENGTH = 64


class ConfigurationError(ValueError):
    """Raised when a configuration file cannot be read or validated."""


@dataclass(frozen=True, slots=True)
class UserConfiguration:
    """A loaded configuration and the path it came from."""

    path: Path
    corrections: dict[str, str]
    exists: bool


def default_config_path() -> Path:
    """Return the platform-neutral per-user configuration path."""
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return base / "cli-autocorrect" / "config.json"


def load_configuration(path: str | Path | None = None) -> UserConfiguration:
    """Load and validate a JSON configuration, or return an empty default."""
    config_path = Path(path).expanduser() if path is not None else default_config_path()
    if not config_path.exists():
        return UserConfiguration(path=config_path, corrections={}, exists=False)
    if not config_path.is_file():
        raise ConfigurationError(f"configuration path is not a file: {config_path}")

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ConfigurationError(f"could not read {config_path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            f"invalid JSON in {config_path} at line {error.lineno}, column {error.colno}"
        ) from error

    if not isinstance(data, dict):
        raise ConfigurationError(f"{config_path} must contain a JSON object")
    unknown_keys = set(data) - {"corrections"}
    if unknown_keys:
        names = ", ".join(sorted(str(key) for key in unknown_keys))
        raise ConfigurationError(f"unknown configuration key(s) in {config_path}: {names}")

    corrections = data.get("corrections", {})
    if not isinstance(corrections, dict):
        raise ConfigurationError(f"'corrections' in {config_path} must be a JSON object")

    validated: dict[str, str] = {}
    for original, replacement in corrections.items():
        if not isinstance(original, str) or not isinstance(replacement, str):
            raise ConfigurationError("correction keys and values must both be strings")
        if not _valid_word(original) or not _valid_word(replacement):
            raise ConfigurationError(
                "corrections must use lowercase ASCII letters only and be at most "
                f"{_MAX_WORD_LENGTH} characters"
            )
        if original == replacement:
            raise ConfigurationError(f"correction maps {original!r} to itself")
        validated[original] = replacement

    return UserConfiguration(path=config_path, corrections=validated, exists=True)


def _valid_word(value: str) -> bool:
    return len(value) <= _MAX_WORD_LENGTH and _PLAIN_WORD.fullmatch(value) is not None
