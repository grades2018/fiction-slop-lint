import unittest
from pathlib import Path

from fiction_slop_lint import analyze, analyze_files
from fiction_slop_lint.engine import Doc

FIX = Path(__file__).parent / "fixtures"


def ids(report, fi=0):
    return [f["rule"] for f in report["files"][fi]["findings"]]


class PatternTests(unittest.TestCase):
    def test_basic_hits_and_positions(self):
        text = "Intro line.\n\nLittle did she know, it was a testament to her patience.\n"
        rep = analyze(text)
        f = {x["rule"]: x for x in rep["files"][0]["findings"]}
        self.assertEqual(f["llm-little-did-she-know"]["line"], 3)
        self.assertEqual(f["llm-little-did-she-know"]["column"], 1)
        self.assertEqual(f["llm-testament-to"]["match"], "a testament to")
        self.assertEqual(f["llm-testament-to"]["line"], 3)

    def test_curly_quotes_and_case(self):
        rep = analyze("She COULDN\u2019T HELP BUT stare.")
        self.assertIn("llm-couldnt-help-but", ids(rep))

    def test_clean_text_has_no_findings(self):
        text = (FIX.parent.parent / "examples" / "02-plain-scene.md").read_text(encoding="utf-8")
        rep = analyze(text)
        self.assertEqual(ids(rep), [])

    def test_masking_of_headings_code_comments_links_and_front_matter(self):
        rep = analyze((FIX / "front_matter.md").read_text(encoding="utf-8"))
        self.assertEqual(ids(rep), [])
        self.assertGreater(rep["files"][0]["words"], 10)

    def test_offsets_survive_masking(self):
        text = "---\nt: x\n---\n\n# Head\n\nIt was a tapestry of lies.\n"
        rep = analyze(text)
        f = [x for x in rep["files"][0]["findings"] if x["rule"] == "llm-tapestry"][0]
        self.assertEqual(f["line"], 7)
        self.assertEqual(f["column"], 10)

    def test_assistant_leak_is_error(self):
        rep = analyze((FIX / "assistant_leak.txt").read_text(encoding="utf-8"))
        leaks = [f for f in rep["files"][0]["findings"] if f["rule"] == "llm-assistant-leak"]
        self.assertGreaterEqual(len(leaks), 2)
        self.assertTrue(all(f["severity"] == "error" for f in leaks))
        self.assertGreaterEqual(rep["summary"]["by_severity"]["error"], 2)

    def test_exclude_list_suppresses_known_false_positive(self):
        rep = analyze('"No," she said only once, and she left.')
        self.assertNotIn("dialogue-adverb-tag", ids(rep))
        rep = analyze('"No," she said firmly, and she left.')
        self.assertIn("dialogue-adverb-tag", ids(rep))

    def test_disable_category_and_min_severity(self):
        text = "Her heart pounded. As an AI language model I cannot help."
        self.assertNotIn("body-heartbeat", ids(analyze(text, disable=["body-heartbeat"])))
        self.assertEqual(set(ids(analyze(text, only_categories=["body-cliche"]))), {"body-heartbeat"})
        rep = analyze(text, min_severity="error")
        self.assertEqual(set(ids(rep)), {"llm-assistant-leak"})


class NearMissTests(unittest.TestCase):
    """Plain sentences that share words with newer phrase rules but should stay clean."""

    def test_palpable_and_sense_of_near_misses(self):
        for text in [
            "She had a good sense of humor.",
            "The sense of smell came back slowly.",
            "A sense of direction would help.",
            "The tension rod fell.",
            "His palpitations eased.",
        ]:
            self.assertNotIn("llm-palpable-sense-of", ids(analyze(text)), text)
        self.assertIn("llm-palpable-sense-of", ids(analyze("A sense of dread crept over him.")))

    def test_maybe_and_first_time_near_misses(self):
        for text in [
            "Maybe she would come back.",
            "Maybe. Just ask him.",
            "For the first time, she spoke.",
            "It was the first time in years that the mill had flooded.",
        ]:
            self.assertNotIn("llm-maybe-just-maybe", ids(analyze(text)), text)
        self.assertIn("llm-maybe-just-maybe", ids(analyze("Perhaps, just perhaps, he lied.")))

    def test_weight_of_literal_near_misses(self):
        for text in [
            "He checked the weight of the cargo on the manifest.",
            "She guessed the weight of her suitcase.",
            "The weight of the anchor was printed on the chain.",
        ]:
            self.assertNotIn("llm-weight-of", ids(analyze(text)), text)
        for text in [
            "She felt the weight of his words.",
            "The weight of the world sat on him.",
            "He carried the weight of it all.",
            "The crushing weight of guilt kept her awake.",
        ]:
            self.assertIn("llm-weight-of", ids(analyze(text)), text)

    def test_air_thick_with_literal_near_misses(self):
        for text in [
            "The air was thick with smoke from the fire.",
            "The air hung heavy with dust after the blast.",
            "The air was thick with mosquitoes by the river.",
        ]:
            self.assertNotIn("llm-air-thick-with", ids(analyze(text)), text)
        for text in [
            "The air was thick with tension.",
            "The air felt heavy with dread.",
        ]:
            self.assertIn("llm-air-thick-with", ids(analyze(text)), text)

    def test_delve_literal_digging_near_misses(self):
        for text in [
            "The archaeologists delved into the barrow.",
            "The miners delved deeper into the mountain.",
            "They delved for gold along the river.",
            "The dwarves delved beneath the earth for a hundred years.",
        ]:
            self.assertNotIn("llm-delve", ids(analyze(text)), text)
        for text in [
            "She decided to delve into the archive.",
            "He delved into the mystery of her past.",
            "Let us delve deeper into the question.",
        ]:
            self.assertIn("llm-delve", ids(analyze(text)), text)

    def test_butterflies_literal_near_misses(self):
        for text in [
            "Butterflies drifted over the meadow all afternoon.",
            "She pinned the butterflies into the display case.",
            "A cloud of white butterflies rose from the lavender.",
        ]:
            self.assertNotIn("body-stomach", ids(analyze(text)), text)
        for text in [
            "He had butterflies before the speech.",
            "Butterflies swirled in her stomach.",
            "Her stomach was full of butterflies.",
            "Seeing him again gave her butterflies.",
        ]:
            self.assertIn("body-stomach", ids(analyze(text)), text)

    def test_tapestry_literal_near_misses(self):
        for text in [
            "The old tapestry hung in the hall.",
            "She took the tapestries down to clean them.",
            "A moth had eaten through the corner of the tapestry.",
        ]:
            self.assertNotIn("llm-tapestry", ids(analyze(text)), text)
        for text in [
            "The city was a rich tapestry of voices.",
            "Their lives were woven into a tapestry of grief.",
            "It was a vibrant tapestry.",
            "The tapestry of the market changed by the hour.",
        ]:
            self.assertIn("llm-tapestry", ids(analyze(text)), text)

    def test_shiver_literal_vibration_near_misses(self):
        for text in [
            "The ice sent a shiver through the hull of the ship.",
            "A shiver ran through the deck as the engines started.",
            "The blast sent a tremor and a shiver through the building.",
        ]:
            self.assertNotIn("llm-shiver-down-spine", ids(analyze(text)), text)
        for text in [
            "A shiver ran down her spine.",
            "The noise sent a chill up his back.",
            "A shiver ran through her.",
            "His voice sent a chill through the room.",
        ]:
            self.assertIn("llm-shiver-down-spine", ids(analyze(text)), text)

    def test_symphony_of_with_the(self):
        for text in [
            "The symphony of birds outside woke her.",
            "The kaleidoscope of feelings would not settle.",
            "A symphony of smells drifted from the market.",
        ]:
            self.assertIn("llm-symphony-of", ids(analyze(text)), text)
        for text in [
            "The orchestra played a symphony by Mahler.",
            "She bought tickets for the symphony on Friday.",
            "He turned the kaleidoscope toward the window.",
        ]:
            self.assertNotIn("llm-symphony-of", ids(analyze(text)), text)

class DensityAndMetricTests(unittest.TestCase):
    def test_density_needs_min_words(self):
        short = "He stopped\u2014then ran\u2014and she followed\u2014slowly\u2014into the dark\u2014alone."
        self.assertNotIn("structure-em-dash-density", ids(analyze(short)))
        longer = short + "\n\n" + "The cat sat on the mat. " * 40
        self.assertIn("structure-em-dash-density", ids(analyze(longer)))

    def test_not_x_but_y_density(self):
        text = ("It wasn't fear, it was dread. It was not anger, but grief. Not just a door, but a threshold.\n\n"
                + "The cat sat on the mat. " * 40)
        self.assertIn("structure-not-x-but-y", ids(analyze(text)))

    def test_repeated_openers_run(self):
        text = "She ran. She hid. She waited. She slept. Then it rained."
        rep = analyze(text)
        f = [x for x in rep["files"][0]["findings"] if x["rule"] == "rep-sentence-openers-run"]
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0]["count"], 4)

    def test_staccato_streak(self):
        rep = analyze("It was dark. He ran. She hid. They fell. Nothing moved. Silence.")
        self.assertIn("rhythm-staccato-streak", ids(rep))

    def test_sentence_monotony(self):
        sent = "The harbor lights flickered on one by one tonight. "
        rep = analyze(sent * 12)
        self.assertIn("rhythm-sentence-monotony", ids(rep))

    def test_varied_rhythm_not_flagged(self):
        text = ("He ran. The corridor, long and lined with portraits of men who had never once smiled, bent left toward the kitchens. "
                "Stop. Why would anyone build a house like this? ") * 4
        self.assertNotIn("rhythm-sentence-monotony", ids(analyze(text)))

    def test_long_sentence(self):
        text = "He walked " + "and walked " * 30 + "home."
        self.assertIn("rhythm-long-sentence", ids(analyze(text)))

    def test_name_frequency(self):
        body = "Sarah looked at the sea. " * 3
        filler = "The wind was cold and the road was long. " * 30
        text = (body + filler + "Then Sarah left, and Sarah's bag stayed. ") * 3
        rep = analyze(text)
        self.assertIn("rep-name-frequency", ids(rep))

    def test_echo_words(self):
        rep = analyze("The lantern swung. Another lantern answered, and a third lantern joined them across the water.")
        self.assertIn("rep-echo-words", ids(rep))

    def test_abbreviations_do_not_split_sentences(self):
        doc = Doc("x", "Dr. Smith met Mr. Jones at St. Mary's. They talked.")
        self.assertEqual(len(doc.sentences), 2)
        doc = Doc("x", "J. K. Smith left. He did.")
        self.assertEqual(len(doc.sentences), 2)

    def test_dialogue_sentence_split(self):
        doc = Doc("x", '"Stop!" he said. "Go on." She went.')
        self.assertEqual(len(doc.sentences), 3)


class CorpusTests(unittest.TestCase):
    def test_ngram_across_chapter_files(self):
        files = [(p.name, p.read_text(encoding="utf-8")) for p in sorted((FIX / "manuscript").glob("*.md"))]
        rep = analyze_files(files)
        phrases = [f["phrase"] for f in rep["corpus"]]
        self.assertTrue(any("nobody crosses the salt flats" in p or "crosses the salt flats after dark" in p for p in phrases), phrases)
        top = rep["corpus"][0]
        self.assertEqual(top["count"], 3)
        self.assertEqual(len(top["locations"]), 3)

    def test_single_file_chapters_via_headings(self):
        text = "\n\n".join("# Chapter %d\n\nThe old clock tower struck midnight again." % i for i in range(1, 4))
        rep = analyze(text)
        self.assertEqual(rep["files"][0]["chapters"], ["Chapter 1", "Chapter 2", "Chapter 3"])
        self.assertTrue(rep["corpus"])

    def test_summary_totals(self):
        rep = analyze("Her heart pounded.\n")
        s = rep["summary"]
        self.assertEqual(s["findings"], 1)
        self.assertEqual(s["by_severity"]["warn"], 1)
        self.assertEqual(s["by_category"], {"body-cliche": 1})


if __name__ == "__main__":
    unittest.main()
