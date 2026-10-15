"""Compare the browser engine (docs/slop.js) with the Python engine using Node."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from fiction_slop_lint import analyze_files
from fiction_slop_lint.rules import load_rules

ROOT = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")

RUNNER = r"""
const fs = require('fs');
const L = require(process.argv[2]);
const rules = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const files = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
process.stdout.write(JSON.stringify(L.analyzeFiles(files, rules)));
"""


def signature(rep):
    return {
        "files": [[(f["rule"], f["offset"], f["match"], f.get("count")) for f in fr["findings"]] for fr in rep["files"]],
        "words": [(fr["words"], fr["sentences"], fr["paragraphs"]) for fr in rep["files"]],
        "corpus": [(f["rule"], f.get("phrase"), f["count"]) for f in rep["corpus"]],
        "summary": rep["summary"],
    }


def stress_text(rules):
    parts = []
    filler = "The cat sat on the mat. " * 30
    for r in rules["rules"]:
        if r["type"] != "metric":
            parts.append(" ".join(r["examples"]))
    parts.append(filler)
    parts.append("# Chapter 2\n\n" + "Sarah looked at the sea. " * 20 + "She ran. She hid. She waited. She slept.\n")
    parts.append('"Stop!" he said. "Go on." Dr. Smith met Mr. Jones. J. K. Smith left.\n')
    parts.append("* * *\n\n> quoted line with a testament to something\n\n```\ncode testament to\n```\n")
    return "\n\n".join(parts)


@unittest.skipUnless(NODE, "node not installed")
class ParityTests(unittest.TestCase):
    def test_python_and_js_agree(self):
        import tempfile
        rules = load_rules()
        paths = sorted((ROOT / "examples").glob("*.md")) + sorted((ROOT / "tests" / "fixtures" / "manuscript").glob("*.md")) \
            + [ROOT / "tests" / "fixtures" / "front_matter.md", ROOT / "tests" / "fixtures" / "assistant_leak.txt"]
        files = [(p.name, p.read_text(encoding="utf-8")) for p in paths]
        files.append(("stress.md", stress_text(rules)))
        with tempfile.TemporaryDirectory() as d:
            runner = Path(d) / "run.js"
            runner.write_text(RUNNER)
            data = Path(d) / "files.json"
            data.write_text(json.dumps([{"path": n, "text": t} for n, t in files]))
            out = subprocess.run([NODE, str(runner), str(ROOT / "docs" / "slop.js"), str(ROOT / "docs" / "rules.json"), str(data)],
                                 check=True, capture_output=True, text=True).stdout
        js = signature(json.loads(out))
        py = signature(analyze_files(files, rules=rules))
        self.assertEqual(py["words"], js["words"])
        self.assertEqual(py["corpus"], js["corpus"])
        for i, (a, b) in enumerate(zip(py["files"], js["files"])):
            self.assertEqual(a, b, "findings differ for %s" % files[i][0])
        self.assertEqual(py["summary"], js["summary"])
        self.assertGreater(py["summary"]["findings"], 100)


if __name__ == "__main__":
    unittest.main()
