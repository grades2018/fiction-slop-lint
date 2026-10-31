# Changelog

## 0.1.2 - 2026-10-31

False positive fixes: eight rules now skip literal uses and keep flagging the figurative ones, and `llm-symphony-of` catches one more form. Rule count is unchanged at 97.

- Version bumped to 0.1.2 (CLI, browser version, SKILL.md, sample reports); the CI example now pins `@v0.1.2`.
- `llm-weight-of` narrowed to figurative objects (words, world, guilt, grief, it all, and similar), so literal uses like "the weight of the cargo" or "the weight of her suitcase" no longer trigger it. Sample reports unchanged.
- Tests: literal near-miss and figurative positive cases for `llm-weight-of`.
- `llm-air-thick-with` no longer flags literal air ("the air was thick with smoke", dust, fog, mist, insects and similar). Mood uses like "thick with tension" still trigger it. Sample reports unchanged.
- Tests: literal near-miss and mood positive cases for `llm-air-thick-with`.
- `llm-tapestry` now flags only figurative uses ("a tapestry of", "a rich tapestry", "woven into a tapestry"), so a literal wall hanging like "the old tapestry hung in the hall" stays clean. Sample reports unchanged.
- Tests: literal near-miss and figurative positive cases for `llm-tapestry`; the masking offset test now uses a figurative sentence.
- `llm-symphony-of` now also catches "the symphony of", "the kaleidoscope of" and "the cacophony of" (it only matched the "a ..." form before), while a literal concert or a real kaleidoscope stays clean.
- Tests: positive and near-miss cases for the "the ..." form of `llm-symphony-of`.
- `llm-shiver-down-spine` no longer flags a literal vibration through an object ("the ice sent a shiver through the hull", "a shiver ran through the deck"). A shiver through a person or a room still triggers it. Sample reports unchanged.
- Tests: literal near-miss and positive cases for `llm-shiver-down-spine`.
- `llm-delve` no longer flags literal digging ("the miners delved deeper into the mountain", "delved into the barrow", "delved for gold"). Figurative uses like "delve into the archive" or "delve into the mystery" still trigger it. Sample reports unchanged.
- Tests: literal near-miss and figurative positive cases for `llm-delve`.
- `body-stomach` no longer flags every mention of butterflies. Literal insects ("butterflies drifted over the meadow", "pinned the butterflies into the display case") stay clean, while "had butterflies", "gave her butterflies" and "butterflies in her stomach" still trigger it. Sample reports unchanged.
- Tests: literal near-miss and figurative positive cases for the butterflies patterns in `body-stomach`.
- `llm-ministrations-orbs` no longer flags every "orbs". Literal objects ("glass orbs hung from the ceiling", "the brass orbs on the bedposts", "three orbs floated above the altar") stay clean, while orbs used for eyes ("her orbs found his", "his emerald orbs narrowed", "their orbs met") still trigger it. Sample reports unchanged.
- Tests: literal near-miss and eye-sense positive cases for `llm-ministrations-orbs`.
- `llm-intricate-labyrinth` no longer flags every "labyrinth". A literal maze ("the minotaur prowled the labyrinth", "the hedge labyrinth behind the manor") stays clean, while "a labyrinth of lies", "the labyrinth of her thoughts" and "labyrinthine" still trigger it. Sample reports unchanged.
- Tests: literal near-miss and figurative positive cases for `llm-intricate-labyrinth`.

## 0.1.1 - 2026-10-21

- New rule `llm-palpable-sense-of` (warn): flags "the tension was palpable" and "a sense of calm washed over her" style emotion labels. 96 rules total.
- New rule `llm-maybe-just-maybe` (warn): flags "maybe, just maybe" and "for the first time in a long time" hope beats. 97 rules total.
- README: llm-phrase category count corrected to 31.
- README: new "Use in CI" section with a minimal GitHub Actions workflow for `--strict`.
- Version bumped to 0.1.1 (CLI, browser version, SKILL.md, sample reports); the CI example now pins `@v0.1.1`.
- Tests: near-miss cases for `llm-palpable-sense-of` and `llm-maybe-just-maybe` (for example "a sense of humor" and "Maybe she would come back." stay clean).

## 0.1.0 - 2026-10-15

First release.

- Python command line tool `fiction-slop-lint` (standard library only) for `.md`, `.txt` and `.docx` files and folders.
- 95 original rules in one editable JSON file: phrase and cliche patterns, density rules and structural metrics.
- Plain text and `--json` reports, `--strict` exit codes with adjustable thresholds.
- Repeated phrase detection across files and chapters.
- Single page browser version in `docs/` that uses the same `rules.json`.
- `SKILL.md` for coding agents.
- Unit tests, including a parity test between the Python and JavaScript engines.
