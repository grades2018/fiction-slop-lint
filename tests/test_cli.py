import io
import json
import os
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from fiction_slop_lint import cli
from fiction_slop_lint.docx_reader import DocxError, docx_to_text

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).parent / "fixtures"


def run(*argv, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    old = cli.sys.stdin
    if stdin is not None:
        cli.sys.stdin = io.StringIO(stdin)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
    finally:
        cli.sys.stdin = old
    return code, out.getvalue(), err.getvalue()


def make_docx(path, paragraphs):
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    body = []
    for style, text in paragraphs:
        ppr = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % style if style else ""
        body.append("<w:p>%s<w:r><w:t xml:space=\"preserve\">%s</w:t></w:r></w:p>" % (ppr, text))
    xml = '<?xml version="1.0" encoding="UTF-8"?><w:document %s><w:body>%s</w:body></w:document>' % (ns, "".join(body))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", xml)


class CliTests(unittest.TestCase):
    def test_text_report_and_exit_zero_without_strict(self):
        code, out, _ = run(str(ROOT / "examples" / "01-cliche-heavy.md"))
        self.assertEqual(code, 0)
        self.assertIn("llm-testament-to", out)
        self.assertIn("Not an AI detector", out)

    def test_json_output_is_valid(self):
        code, out, _ = run("--json", str(FIX / "assistant_leak.txt"))
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["tool"], "fiction-slop-lint")
        self.assertGreaterEqual(data["summary"]["by_severity"]["error"], 2)

    def test_strict_fails_on_errors_and_passes_on_clean(self):
        code, out, _ = run("--strict", str(FIX / "assistant_leak.txt"))
        self.assertEqual(code, 1)
        self.assertIn("strict: FAIL", out)
        code, out, _ = run("--strict", str(ROOT / "examples" / "02-plain-scene.md"))
        self.assertEqual(code, 0)
        self.assertIn("strict: PASS", out)

    def test_strict_thresholds_are_adjustable(self):
        f = str(ROOT / "examples" / "01-cliche-heavy.md")
        self.assertEqual(run("--strict", f)[0], 1)
        code, _, _ = run("--strict", "--max-errors", "99", "--max-warnings", "999", "--max-per-1000", "999", f)
        self.assertEqual(code, 0)

    def test_folder_is_walked_in_natural_order(self):
        code, out, _ = run("--json", str(FIX / "manuscript"))
        data = json.loads(out)
        self.assertEqual([os.path.basename(f["path"]) for f in data["files"]], ["ch1.md", "ch2.md", "ch3.md"])
        self.assertTrue(data["corpus"])

    def test_stdin(self):
        code, out, _ = run("-", stdin="A testament to patience.")
        self.assertEqual(code, 0)
        self.assertIn("<stdin>", out)

    def test_errors(self):
        self.assertEqual(run()[0], 2)
        code, _, err = run("/no/such/file.md")
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)
        self.assertEqual(run("--disable", "not-a-rule", str(FIX / "assistant_leak.txt"))[0], 2)
        self.assertEqual(run("--rules", "/no/such.json", "x.md")[0], 2)

    def test_list_rules(self):
        code, out, _ = run("--list-rules")
        self.assertEqual(code, 0)
        self.assertIn("llm-testament-to", out)
        code, out, _ = run("--list-rules", "--markdown")
        self.assertIn("| Rule id |", out)

    def test_custom_rules_file(self):
        with tempfile.TemporaryDirectory() as d:
            rp = os.path.join(d, "r.json")
            with open(rp, "w") as fh:
                json.dump({"categories": {"x": "x"}, "rules": [
                    {"id": "no-purple", "category": "x", "severity": "warn", "type": "pattern",
                     "message": "purple", "patterns": ["\\bpurple\\b"]}]}, fh)
            code, out, _ = run("--json", "--rules", rp, "-", stdin="A purple door.")
            data = json.loads(out)
            self.assertEqual([f["rule"] for f in data["files"][0]["findings"]], ["no-purple"])

    def test_exclude_glob(self):
        code, out, _ = run("--json", "--exclude", "ch2*", str(FIX / "manuscript"))
        data = json.loads(out)
        self.assertEqual(len(data["files"]), 2)


class DocxTests(unittest.TestCase):
    def test_docx_text_and_headings(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "book.docx")
            make_docx(p, [("Heading1", "Chapter 1"), (None, "Her heart pounded &amp; she waited."), (None, "")])
            text = docx_to_text(p)
            self.assertIn("# Chapter 1", text)
            self.assertIn("Her heart pounded & she waited.", text)
            code, out, _ = run("--json", p)
            data = json.loads(out)
            self.assertEqual(data["files"][0]["chapters"], ["Chapter 1"])
            self.assertIn("body-heartbeat", [f["rule"] for f in data["files"][0]["findings"]])

    def test_bad_docx(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bad.docx")
            with open(p, "wb") as fh:
                fh.write(b"not a zip")
            with self.assertRaises(DocxError):
                docx_to_text(p)
            self.assertEqual(run(p)[0], 2)


if __name__ == "__main__":
    unittest.main()
