import json
import re
import unittest
from pathlib import Path

from fiction_slop_lint.rules import RulesError, load_rules, validate_rules

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT / "fiction_slop_lint" / "data" / "rules.json"


class RulesFileTests(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules()

    def test_rule_count_in_range(self):
        n = len(self.rules["rules"])
        self.assertGreaterEqual(n, 60)
        self.assertLessEqual(n, 100)

    def test_ids_unique_and_categories_declared(self):
        ids = [r["id"] for r in self.rules["rules"]]
        self.assertEqual(len(ids), len(set(ids)))
        for r in self.rules["rules"]:
            self.assertIn(r["category"], self.rules["categories"])

    def test_every_pattern_rule_has_examples_that_match(self):
        from fiction_slop_lint.engine import Doc, _compile, _matches
        for r in self.rules["rules"]:
            if r["type"] == "metric":
                continue
            self.assertTrue(r.get("examples"), "%s has no examples" % r["id"])
            compiled = _compile(r)
            for ex in r["examples"]:
                doc = Doc("x", ex)
                self.assertTrue(_matches(doc, r, compiled), "%s does not match its example %r" % (r["id"], ex))

    def test_density_rules_trigger_when_padded(self):
        from fiction_slop_lint import analyze
        filler = "The cat sat on the mat. " * 60
        for r in self.rules["rules"]:
            if r["type"] != "density":
                continue
            text = " ".join(r["examples"]) + "\n\n" + filler
            rep = analyze(text, rules=self.rules, only_categories=[r["category"]])
            ids = [f["rule"] for f in rep["files"][0]["findings"]]
            self.assertIn(r["id"], ids, "density rule %s did not fire on its padded example" % r["id"])

    def test_no_em_dashes_in_rules(self):
        raw = RULES_PATH.read_text(encoding="utf-8")
        self.assertNotIn("\u2014", raw)

    def test_web_copy_in_sync(self):
        a = RULES_PATH.read_text(encoding="utf-8")
        b = (ROOT / "docs" / "rules.json").read_text(encoding="utf-8")
        self.assertEqual(a, b, "docs/rules.json differs from the packaged rules; run tools/sync_rules.py")

    def test_validation_rejects_bad_rules(self):
        base = {"rules": [{"id": "x", "category": "c", "severity": "warn", "type": "pattern", "message": "m", "patterns": ["("]}]}
        with self.assertRaises(RulesError):
            validate_rules(base)
        with self.assertRaises(RulesError):
            validate_rules({"rules": [{"id": "x", "severity": "loud", "type": "pattern", "message": "m", "patterns": ["a"]}]})
        with self.assertRaises(RulesError):
            validate_rules({"rules": [{"id": "x", "severity": "warn", "type": "metric", "metric": "nope", "message": "m", "params": {}},]})
        dup = {"rules": [{"id": "x", "severity": "warn", "type": "pattern", "message": "m", "patterns": ["a"]}] * 2}
        with self.assertRaises(RulesError):
            validate_rules(dup)


if __name__ == "__main__":
    unittest.main()


class PublicTextStyleTests(unittest.TestCase):
    def test_no_em_dashes_in_public_text(self):
        bad = []
        for pattern in ("*.md", "*.txt", "*.json", "*.html", "*.js", "*.py", "*.toml", "*.yml"):
            for p in ROOT.rglob(pattern):
                if any(part in (".git", "__pycache__", "build") or part.endswith(".egg-info") for part in p.parts):
                    continue
                if "\u2014" in p.read_text(encoding="utf-8"):
                    bad.append(str(p.relative_to(ROOT)))
        self.assertEqual(bad, [])
