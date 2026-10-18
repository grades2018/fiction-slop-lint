# Changelog

## Unreleased

- New rule `llm-palpable-sense-of` (warn): flags "the tension was palpable" and "a sense of calm washed over her" style emotion labels. 96 rules total.
- New rule `llm-maybe-just-maybe` (warn): flags "maybe, just maybe" and "for the first time in a long time" hope beats. 97 rules total.
- README: llm-phrase category count corrected to 31.

## 0.1.0 - 2026-10-15

First release.

- Python command line tool `fiction-slop-lint` (standard library only) for `.md`, `.txt` and `.docx` files and folders.
- 95 original rules in one editable JSON file: phrase and cliche patterns, density rules and structural metrics.
- Plain text and `--json` reports, `--strict` exit codes with adjustable thresholds.
- Repeated phrase detection across files and chapters.
- Single page browser version in `docs/` that uses the same `rules.json`.
- `SKILL.md` for coding agents.
- Unit tests, including a parity test between the Python and JavaScript engines.
