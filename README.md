# CLI Autocorrect

[![CI](https://github.com/harshu11-ai/CLI-Autocorrect/actions/workflows/ci.yml/badge.svg)](https://github.com/harshu11-ai/CLI-Autocorrect/actions/workflows/ci.yml)

CLI Autocorrect fixes high-confidence typos while you type prompts in
[Claude Code](https://docs.anthropic.com/en/docs/claude-code) and the
[Codex CLI](https://github.com/openai/codex). It runs locally and wraps the
existing CLI—you keep using the normal Claude or Codex interface.

```text
can you fix teh fucntion
                ↓
can you fix the function
```

Corrections happen after Space or Enter. The wrapped application receives
ordinary backspace and replacement keystrokes, as if you corrected the word
yourself.

## Features

- local English correction with no network requests or telemetry
- built specifically for Claude Code and Codex CLI
- common typo, transposition, extra-character, and high-confidence spelling fixes
- protection for paths, URLs, flags, identifiers, and mixed alphanumeric terms
- pasted text passed through unchanged
- immediate Backspace to undo the last correction
- optional personal corrections and abbreviation expansions in a small JSON config file
- transparent `--no-corrections` mode for terminal troubleshooting

## Requirements

- macOS or Linux
- Python 3.10 or newer
- Claude Code and/or Codex CLI already installed and available on `PATH`

## Install

For a clean, isolated command-line installation, use
[pipx](https://pipx.pypa.io/):

```bash
pipx install git+https://github.com/harshu11-ai/CLI-Autocorrect.git
```

Or install it in a virtual environment with pip:

```bash
git clone https://github.com/harshu11-ai/CLI-Autocorrect.git
cd CLI-Autocorrect
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Verify the installation:

```bash
cli-autocorrect --doctor
```

The doctor reports the Python and platform versions, local dictionary status,
config path, terminal status, and whether `claude` and `codex` are on `PATH`.

## Usage

Launch either supported application through the wrapper:

```bash
cli-autocorrect claude
cli-autocorrect codex
```

Arguments after the application name are passed through unchanged:

```bash
cli-autocorrect codex --model MODEL_NAME
```

To test the PTY wrapper without corrections or abbreviation expansions:

```bash
cli-autocorrect --no-corrections codex
```

Wrapper options such as `--config` and `--no-corrections` must come before the
application name. Everything after `claude` or `codex` belongs to that app.

## Personal corrections and abbreviations

Create `~/.config/cli-autocorrect/config.json` to add spelling corrections and
abbreviations specific to your typing:

```json
{
  "corrections": {
    "awsome": "awesome",
    "reccomend": "recommend"
  },
  "abbreviations": {
    "pr": "pull request",
    "runt": "run the test suite",
    "expfn": "explain this function step by step"
  }
}
```

Typing `pr ` now inserts `pull request `. Abbreviations expand after Space or
Enter, preserve trailing punctuation, and never recursively expand generated
text. Immediate Backspace removes the expansion and restores its trigger.

Correction keys and values, and abbreviation keys, must be lowercase words
containing only ASCII letters. Abbreviation values may contain 1–500 printable
ASCII characters, including spaces and punctuation, but cannot have surrounding
spaces. A key cannot appear in both sections. Invalid configuration is reported
clearly before the wrapped CLI starts.

The wrapper inserts configured expansion text as keystrokes; it does not invoke
a shell or interpret the expansion itself. Pasted abbreviations are not expanded.

Use another file for one session with:

```bash
cli-autocorrect --config /path/to/config.json claude
```

On systems that set `XDG_CONFIG_HOME`, the default file is stored beneath that
directory instead of `~/.config`.

## Safety model

CLI Autocorrect prefers missing a typo over changing code or technical terms.
It does not correct:

- pasted content
- paths, URLs, email addresses, and command-line flags
- `camelCase`, `snake_case`, and `kebab-case`
- uppercase or mixed-alphanumeric tokens
- ambiguous words without a clearly preferred correction
- the rest of a line after cursor movement or an unknown terminal escape sequence

For example, `wnat` remains unchanged because both “want” and “what” are
plausible. Pressing Backspace immediately after a correction restores the
original word.

## Current boundaries

This release corrects completed, lowercase English words and expands exact,
user-defined lowercase abbreviation triggers. It intentionally does not rewrite
grammar, split merged words such as `toteh`, repair misplaced spaces, or modify
text that was pasted. Those changes need stronger context and more guardrails
than ordinary spelling correction.

The PTY wrapper has been smoke-tested with Codex CLI 0.151.0 and Claude Code
2.1.252 on macOS. Compatibility is continuously tested on macOS and Linux, but
interactive terminal behavior can still differ between terminal emulators.

## Development

Install the project and its development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the same checks used by CI:

```bash
python -m ruff check .
python -m unittest discover -s tests -v
python -m build
python -m twine check dist/*
```

The package uses a small correction-engine interface, so the spelling engine
can be replaced without changing the terminal input processor.

## Privacy

Prompts are processed in memory on the local machine. CLI Autocorrect does not
store prompts, terminal output, environment variables, or source code.

## License

[MIT](LICENSE)
