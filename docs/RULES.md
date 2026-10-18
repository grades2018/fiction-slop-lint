# Rule list

Generated with `fiction-slop-lint --list-rules --markdown`. Severity: `error` for leftovers that should never ship, `warn` for strong tells, `info` for softer hints.

| Rule id | Category | Severity | Type | What it flags |
|---|---|---|---|---|
| `llm-testament-to` | llm-phrase | warn | pattern | Stock praise phrase. A plain verb usually says it better. |
| `llm-tapestry` | llm-phrase | warn | pattern | 'Tapestry' is a frequent figurative filler. |
| `llm-shiver-down-spine` | llm-phrase | warn | pattern | Shiver-down-the-spine beat. |
| `llm-little-did-she-know` | llm-phrase | warn | pattern | Narrator-wink foreshadowing. |
| `llm-eyes-sparkled` | llm-phrase | warn | pattern | Sparkling, twinkling or dancing eyes. |
| `llm-breath-not-know` | llm-phrase | warn | pattern | The breath-you-did-not-know-you-were-holding line. |
| `llm-barely-whisper` | llm-phrase | warn | pattern | Barely-above-a-whisper voice. |
| `llm-delve` | llm-phrase | warn | pattern | 'Delve' is a very frequent assistant-style verb. |
| `llm-realm-of` | llm-phrase | info | pattern | 'Realm of' as filler. |
| `llm-air-thick-with` | llm-phrase | warn | pattern | Air thick with tension, heavy with something. |
| `llm-palpable-sense-of` | llm-phrase | warn | pattern | Palpable tension, or a sense of something washing over a character. |
| `llm-symphony-of` | llm-phrase | warn | pattern | Symphony, kaleidoscope or dance of abstractions. |
| `llm-myriad` | llm-phrase | info | pattern | 'Myriad' is a frequent filler. |
| `llm-beacon-of-hope` | llm-phrase | warn | pattern | Beacon of hope, ray of light. |
| `llm-whispers-of` | llm-phrase | info | pattern | Whispers of the past or ancient things. |
| `llm-ethereal-vocab` | llm-phrase | info | pattern | Vague elevated adjectives. |
| `llm-mix-of-emotions` | llm-phrase | warn | pattern | 'A mix of X and Y' emotion label. |
| `llm-couldnt-help-but` | llm-phrase | warn | pattern | 'Couldn't help but' is a weak filler construction. |
| `llm-wave-of-emotion` | llm-phrase | warn | pattern | A wave, rush or surge of emotion. |
| `llm-weight-of` | llm-phrase | info | pattern | The weight of something as a figurative load. |
| `llm-exhale-breath` | llm-phrase | warn | pattern | Let out a slow breath, a shaky exhale. |
| `llm-emotion-etched` | llm-phrase | warn | pattern | Emotion etched, flickered or crossed a face. |
| `llm-moral-ending` | llm-phrase | warn | pattern | Tidy lesson or 'journey just begun' closing line. |
| `llm-maybe-just-maybe` | llm-phrase | warn | pattern | 'Maybe, just maybe' hope beat, or 'for the first time in a long time'. |
| `llm-foreshadow-cliche` | llm-phrase | info | pattern | Stock ominous foreshadowing. |
| `llm-stock-character-names` | llm-phrase | info | pattern | Names that language models reach for by default. Fine if intentional. |
| `llm-stock-place-names` | llm-phrase | info | pattern | Place names that language models reach for by default. |
| `llm-ministrations-orbs` | llm-phrase | info | pattern | Over-poetic words for ordinary things. |
| `llm-intricate-labyrinth` | llm-phrase | info | pattern | Intricate web, labyrinth, dance. |
| `llm-assistant-leak` | llm-phrase | error | pattern | Chatbot or editing-prompt text left in the manuscript. |
| `llm-meta-narration` | llm-phrase | warn | pattern | Narrator addressing the reader or announcing the theme. |
| `body-heartbeat` | body-cliche | warn | pattern | Heart pounding, racing or skipping. |
| `body-breath-caught` | body-cliche | warn | pattern | Breath catching or hitching. |
| `body-jaw` | body-cliche | warn | pattern | Clenched, tightened or ticking jaw. |
| `body-knuckles-white` | body-cliche | warn | pattern | White knuckles. |
| `body-stomach` | body-cliche | warn | pattern | Stomach dropping, churning or knotting. |
| `body-eyes-gesture` | body-cliche | warn | pattern | Narrowing, widening, flashing or rolling eyes. |
| `body-gave-a-nod` | body-cliche | info | pattern | 'Gave a small nod/shrug/smile' light-verb beat. |
| `body-lips-smile` | body-cliche | warn | pattern | Lips curving, smile tugging. |
| `body-hand-hair` | body-cliche | warn | pattern | Running a hand through hair or down the face. |
| `body-throat-lump` | body-cliche | warn | pattern | Swallowing hard, lump in the throat. |
| `body-chill-goosebumps` | body-cliche | warn | pattern | Goosebumps, chills, raised neck hairs. |
| `body-tears` | body-cliche | warn | pattern | Tears pricking, welling or spilling. |
| `body-tired-gestures` | body-cliche | info | pattern | Pinching the nose bridge, rubbing the temples. |
| `body-time-stopped` | body-cliche | warn | pattern | Time slowing or the world falling away. |
| `body-voice-quality` | body-cliche | info | pattern | Voice cracking, wavering, dropping. |
| `body-silence` | body-cliche | warn | pattern | Silence stretching, hanging or settling. |
| `body-hung-in-air` | body-cliche | warn | pattern | Words or tension hanging in the air. |
| `body-shoulders-tense` | body-cliche | info | pattern | Shoulders tensing, sagging or squaring. |
| `simile-cold-as-ice` | simile-cliche | warn | pattern | Stock temperature or colour simile. |
| `simile-animal-stock` | simile-cliche | warn | pattern | Stock animal comparisons. |
| `simile-quiet-as` | simile-cliche | info | pattern | Quiet-as-the-grave style simile. |
| `simile-sharp-as` | simile-cliche | info | pattern | Sharp-as-a-razor style simile. |
| `simile-punch-to-gut` | simile-cliche | warn | pattern | Like a punch or knife to the gut. |
| `simile-light-shadow` | simile-cliche | warn | pattern | Dancing light, creeping shadow. |
| `simile-weather-sky` | simile-cliche | info | pattern | Stock sky and weather lines. |
| `simile-stock-comparison` | simile-cliche | info | pattern | Over-used time and speed comparisons. |
| `simile-opening-cliche` | simile-cliche | info | pattern | Wake-up, alarm or mirror scene opening. |
| `dialogue-adverb-tag` | dialogue | warn | pattern | Adverb attached to a speech tag. |
| `dialogue-ly-density` | dialogue | info | density | High density of -ly adverbs. |
| `dialogue-bookisms` | dialogue | info | pattern | Showy speech verbs in place of 'said'. |
| `dialogue-nonspeech-tag` | dialogue | warn | pattern | Smile, nod or sigh used as a speech tag. |
| `dialogue-voice-tag-tail` | dialogue | info | pattern | Tag followed by a voice description clause. |
| `dialogue-on-the-nose` | dialogue | info | pattern | Stock on-the-nose dialogue lines. |
| `dialogue-air-quotes-meta` | dialogue | info | pattern | Dialogue that announces its own emotion. |
| `telling-filter-words` | telling | info | density | Many perception and cognition filter words. |
| `telling-hedging` | telling | info | density | Frequent hedging constructions. |
| `telling-named-emotion` | telling | info | pattern | Emotion stated directly as a label. |
| `telling-intensifiers` | telling | info | density | Frequent intensifiers. |
| `telling-suddenly` | telling | info | density | Sudden-event markers used repeatedly. |
| `telling-began-to` | telling | info | density | 'Began to' and 'started to' weaken verbs. |
| `telling-vague-something` | telling | warn | pattern | Vague 'something shifted/unreadable' phrasing. |
| `telling-epiphany` | telling | warn | pattern | Announced realization. |
| `telling-rule-of-three` | telling | info | density | Frequent three-item lists. |
| `summary-time-skip` | summary | info | pattern | Summary time-skip phrasing in place of a scene. |
| `summary-routine` | summary | info | pattern | Habitual routine summary. |
| `summary-backstory-markers` | summary | info | density | Dense backstory markers. |
| `summary-memory-flood` | summary | info | pattern | Memories flooding back. |
| `summary-character-label` | summary | info | pattern | Character introduced by a type label. |
| `summary-scene-opening-weather` | summary | info | pattern | Scene opening with a stock time or weather line. |
| `structure-em-dash-density` | structure | warn | density | Heavy use of dashes as punctuation. |
| `structure-ellipsis-density` | structure | info | density | Frequent ellipses. |
| `structure-not-x-but-y` | structure | warn | density | Frequent 'not X, but Y' or 'it wasn't X, it was Y' contrast pattern. |
| `structure-ing-opener` | structure | info | density | Many sentences opening with an -ing participle. |
| `structure-asking-narrator` | structure | info | pattern | Rhetorical question aimed at the reader. |
| `structure-colon-reveal` | structure | info | pattern | Colon followed by a dramatic reveal. |
| `rep-sentence-openers-run` | repetition | warn | metric | Several sentences in a row open with the same word. |
| `rep-sentence-opener-share` | repetition | info | metric | One word opens a large share of the sentences. |
| `rep-ngram-phrases` | repetition | warn | metric | Phrase repeats often or in several chapters. |
| `rep-name-frequency` | repetition | info | metric | A name appears very often. |
| `rep-echo-words` | repetition | info | metric | Same uncommon word three times in a short stretch. |
| `rhythm-sentence-monotony` | rhythm | warn | metric | Sentence lengths barely vary over a long stretch. |
| `rhythm-paragraph-monotony` | rhythm | info | metric | Paragraphs are nearly the same length for a long stretch. |
| `rhythm-staccato-streak` | rhythm | warn | metric | Run of very short sentences inside one paragraph. |
| `rhythm-long-sentence` | rhythm | info | metric | Very long sentence. |
| `rhythm-one-line-paragraphs` | rhythm | info | metric | Large share of one-sentence narrative paragraphs. |
| `rhythm-punchline-endings` | rhythm | warn | metric | Many paragraphs end on a very short punch sentence after a long one. |

97 rules in 9 categories.
