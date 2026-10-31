---
name: fiction-slop-lint
description: Run an offline style linter over a fiction manuscript (Markdown, plain text or Word files) to find cliches, overused phrases, repeated phrases across chapters and rhythm habits, then report them with line numbers. Use when a user wants a style check of a novel or story draft. It is a style linter, not an AI detector.
---

# fiction-slop-lint

A zero-dependency Python command line tool that lints fiction for stock phrases, cliche beats, repetition and rhythm habits. It reads `.md`, `.txt` and `.docx` files or whole folders and prints a plain text or JSON report.

## When to use

- The user asks for a style pass, a "cliche check", or a repetition check on a manuscript or chapter folder.
- Before sending a draft to an editor or beta readers.
- To find leftover chatbot text such as "Certainly! Here is the revised chapter" in a draft (rule `llm-assistant-leak`, severity `error`).

## When not to use, and what not to claim

- Do not present results as AI detection or as proof of who or what wrote the text. Findings are style hints with known false positives.
- Do not offer it as a way to hide AI use or to avoid platform disclosure rules. Amazon KDP, for example, requires authors to disclose AI-generated text when publishing. Tell the user that if the topic comes up.
- Do not rewrite the author's prose automatically just to clear findings. Report them, explain the likely issue, and let the author decide.

## Install

```
pip install git+https://github.com/grades2018/fiction-slop-lint
```

Or run from a clone without installing: `python -m fiction_slop_lint ...` from the repo root. Python 3.9 or newer, no other packages.

## Run

```
# one file
fiction-slop-lint chapter-01.md

# a manuscript folder (recurses, natural sort: ch2 before ch10)
fiction-slop-lint manuscript/

# machine readable
fiction-slop-lint manuscript/ --json > slop-report.json

# CI style gate (exit code 1 when thresholds are exceeded)
fiction-slop-lint manuscript/ --strict --max-warnings 25 --max-per-1000 8
```

Useful options: `-v` (context and tips), `--min-severity warn`, `--category body-cliche,llm-phrase`, `--disable RULE_ID,...`, `--exclude "notes*"`, `--rules my-rules.json`, `--list-rules`.

Exit codes: `0` ok, `1` strict thresholds exceeded, `2` usage or input error.

## Suggested workflow for an agent

1. Run with `--json` on the folder and keep the output.
2. Summarize `summary.by_severity` and `summary.warn_and_error_per_1000_words`.
3. Handle `error` findings first (leftover assistant text). Then `warn`. Treat `info` as optional.
4. Look at `corpus` entries (phrases repeated across chapters or files) and list them with their first locations.
5. For the top issues per file, quote the `context`, name the `rule`, and give the `suggestion` in plain words. Ask the author before editing anything.
6. Remind the user about false positives: dialogue, deliberate repetition, genre conventions and first-person narration can all trigger rules legitimately.

## JSON shape (abridged)

```
{
  "tool": "fiction-slop-lint", "version": "0.1.2",
  "files": [{"path": "...", "words": 0, "sentences": 0, "chapters": ["..."],
             "findings": [{"rule": "llm-testament-to", "category": "llm-phrase", "severity": "warn",
                            "message": "...", "line": 3, "column": 29, "match": "...", "context": "...",
                            "suggestion": "..."}]}],
  "corpus": [{"rule": "rep-ngram-phrases", "phrase": "...", "count": 3, "locations": [{"file": "...", "line": 5}]}],
  "summary": {"files": 1, "words": 0, "findings": 0, "by_severity": {"error": 0, "warn": 0, "info": 0},
              "by_category": {}, "warn_and_error_per_1000_words": 0.0}
}
```

Density findings (for example `structure-em-dash-density`) carry `count`, `rate` and `limit` instead of one finding per hit. Line numbers for `.docx` files refer to the text extracted from the document, not Word's own pagination.

## Editing rules

Rules are plain JSON in `fiction_slop_lint/data/rules.json`. Users can pass their own file with `--rules`. See CONTRIBUTING.md for the rule format.
