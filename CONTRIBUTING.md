# Contributing

Thanks for helping. This is a small project; the bar is "useful and honest".

## Ground rules

- fiction-slop-lint is a **style linter**. It must never be described as an AI detector, and rules must not be justified by "this is how detectors work".
- Rules are original text. Please do not paste rule lists, regexes or code from other projects. Write your own patterns from your own reading.
- Every rule should come with a sentence that shows where it misfires. If a rule flags too much good prose, make it narrower or lower its severity.
- Keep the tool dependency free (standard library only) and offline.

## Setup

```
git clone https://github.com/grades2018/fiction-slop-lint
cd fiction-slop-lint
python -m unittest discover -s tests -t .
```

Node 18+ is optional but recommended: it enables the parity test that compares the Python engine with `docs/slop.js`.

## Editing rules

Rules live in `fiction_slop_lint/data/rules.json`.

- `pattern` rules flag every match. `density` rules flag once when a pattern passes a per-1000-word limit. `metric` rules call a built-in measurement with parameters.
- Patterns are case-insensitive regular expressions that must work in both Python and JavaScript. Stick to `\b`, groups, alternation, quantifiers and character classes. No lookbehind, no inline flags.
- Every `pattern` and `density` rule needs an `examples` list of text that the rule must match. The tests check this.
- After editing, run `python tools/sync_rules.py` to copy the file to `docs/rules.json`, then run the tests.
- Keep message and suggestion text free of em dashes (use commas, periods or hyphens).

## Changing an algorithm

The Python engine (`fiction_slop_lint/engine.py`) and the browser engine (`docs/slop.js`) implement the same algorithms. Change both, and let `tests/test_js_parity.py` confirm they still agree.

## Pull requests

Small, focused PRs are easiest. Mention the rule ids you touched. By contributing you agree your work is released under the MIT license.
