# CLI Autocorrect

CLI Autocorrect is an experimental, local autocorrect layer for prompts typed
into [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and the
[Codex CLI](https://github.com/openai/codex).

```text
can you fix teh fucntion
                ↓
can you fix the function
```

The correction happens when a token is completed with Space or Enter.
The child application receives ordinary backspace and replacement keystrokes,
as though the user corrected the typo manually.

> [!WARNING]
> This project is a pre-alpha PTY prototype. Use the explicit wrapper while its
> terminal compatibility is being validated.

## Current scope

- Claude Code and Codex CLI only
- macOS and Linux
- small, high-confidence English typo map
- unique adjacent-character transpositions
- unambiguous single extra-character mistakes
- strict, local frequency-ranked spelling for broader mistakes
- protection for paths, URLs, flags, identifiers, and mixed alphanumeric terms
- bracketed paste passed through unchanged
- Backspace immediately after a correction restores the original token
- no network requests, telemetry, or prompt storage

The token processor depends on a small `CorrectionEngine` interface. Curated
rules handle immediate common mistakes while a local SymSpell frequency
dictionary loads in the background for broader high-confidence corrections.

## Install for development

Python 3.10 or newer is required.

```bash
git clone https://github.com/harshu11-ai/CLI-Autocorrect.git
cd CLI-Autocorrect
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Usage

Run either supported application through the wrapper:

```bash
cli-autocorrect claude
cli-autocorrect codex
```

Arguments after the application name are passed to it:

```bash
cli-autocorrect codex --model MODEL_NAME
```

To test PTY behavior without modifying input:

```bash
cli-autocorrect --no-corrections codex
```

Transparent `claude` and `codex` shell integration will be added only after the
explicit wrapper is reliable.

## Compatibility

The PTY wrapper and correction rendering have been manually smoke-tested with:

- Codex CLI 0.151.0 on macOS
- Claude Code 2.1.252 on macOS

Compatibility tests did not submit prompts or invoke a model.

## Safety policy

The engine prefers a missed typo to an incorrect replacement. It currently
abstains from correcting:

- unknown or ambiguous words
- pasted content
- paths and URLs
- command-line flags
- `camelCase`, `snake_case`, and `kebab-case`
- uppercase and mixed-alphanumeric tokens
- the remainder of a line after cursor movement or an unknown escape sequence

For example, `wnat` is not corrected because both “want” and “what” are
plausible without sentence-level context.

## Run tests

The test suite uses only the Python standard library:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Privacy

All processing happens in memory on the local machine. CLI Autocorrect makes no
network requests and does not persist prompts, terminal output, environment
variables, or source code.

## Project status

The current goal is to validate transparent terminal behavior in real Claude
Code and Codex sessions. Broader spellchecking, personalized dictionaries, and
automatic shell shims come after that feasibility gate.
