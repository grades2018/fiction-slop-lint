"""Command line interface."""

import argparse
import fnmatch
import os
import re
import sys

from . import __version__
from .docx_reader import DocxError, docx_to_text
from .engine import analyze_files
from .report import render_json, render_rules_markdown, render_rules_text, render_text
from .rules import RulesError, load_rules

EXTS = (".md", ".markdown", ".txt", ".docx")


def _natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def gather(paths, excludes=()):
    files = []
    for p in paths:
        if p == "-":
            files.append("-")
        elif os.path.isdir(p):
            found = []
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for n in names:
                    if n.lower().endswith(EXTS) and not n.startswith(".") and not n.startswith("~$"):
                        found.append(os.path.join(root, n))
            files.extend(sorted(found, key=_natural))
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise FileNotFoundError(p)
    if excludes:
        files = [f for f in files if f == "-" or not any(fnmatch.fnmatch(f, e) or fnmatch.fnmatch(os.path.basename(f), e) for e in excludes)]
    return files


def read_text(path):
    if path == "-":
        return sys.stdin.read()
    if path.lower().endswith(".docx"):
        return docx_to_text(path)
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    return data.decode("cp1252", errors="replace")


def build_parser():
    ap = argparse.ArgumentParser(
        prog="fiction-slop-lint",
        description="Offline style linter for fiction manuscripts. Flags overused AI-flavoured phrasing and common "
                    "cliches, repetition and rhythm habits. It is a style linter, not an AI detector.",
        epilog="Exit codes: 0 ok, 1 strict thresholds exceeded, 2 usage or input error.")
    ap.add_argument("paths", nargs="*", help="files or folders (.md, .txt, .docx); '-' reads stdin")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--strict", action="store_true", help="exit 1 when thresholds are exceeded")
    ap.add_argument("--max-errors", type=int, default=0, help="strict: allowed error findings (default 0)")
    ap.add_argument("--max-warnings", type=int, default=25, help="strict: allowed warning findings (default 25)")
    ap.add_argument("--max-per-1000", type=float, default=8.0,
                    help="strict: allowed warnings+errors per 1000 words (default 8.0)")
    ap.add_argument("--rules", metavar="FILE", help="use this rules JSON instead of the built-in one")
    ap.add_argument("--disable", metavar="IDS", default="", help="comma separated rule ids to skip")
    ap.add_argument("--category", metavar="CATS", default="", help="comma separated categories to run (default all)")
    ap.add_argument("--min-severity", choices=("info", "warn", "error"), default="info")
    ap.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="skip files matching GLOB (repeatable)")
    ap.add_argument("-v", "--verbose", action="store_true", help="show context and suggestions")
    ap.add_argument("--list-rules", action="store_true", help="list rules and exit (add --json or --markdown)")
    ap.add_argument("--markdown", action="store_true", help="with --list-rules, print a Markdown table")
    ap.add_argument("--version", action="version", version="fiction-slop-lint " + __version__)
    return ap


def _split(s):
    return [x.strip() for x in s.split(",") if x.strip()]


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        rules = load_rules(args.rules)
    except (OSError, RulesError) as exc:
        print("fiction-slop-lint: %s" % exc, file=sys.stderr)
        return 2
    if args.list_rules:
        if args.json:
            import json
            print(json.dumps(rules, indent=2))
        elif args.markdown:
            sys.stdout.write(render_rules_markdown(rules))
        else:
            sys.stdout.write(render_rules_text(rules))
        return 0
    if not args.paths:
        print("fiction-slop-lint: no input. Give files or folders, or '-' for stdin. Try --help.", file=sys.stderr)
        return 2
    known = {r["id"] for r in rules["rules"]}
    disable = _split(args.disable)
    bad = [d for d in disable if d not in known]
    if bad:
        print("fiction-slop-lint: unknown rule id(s) in --disable: %s" % ", ".join(bad), file=sys.stderr)
        return 2
    cats = _split(args.category)
    badc = [c for c in cats if c not in rules.get("categories", {})]
    if badc:
        print("fiction-slop-lint: unknown category: %s" % ", ".join(badc), file=sys.stderr)
        return 2
    try:
        paths = gather(args.paths, args.exclude)
    except FileNotFoundError as exc:
        print("fiction-slop-lint: no such file or folder: %s" % exc, file=sys.stderr)
        return 2
    if not paths:
        print("fiction-slop-lint: no .md, .txt or .docx files found", file=sys.stderr)
        return 2
    files = []
    try:
        for p in paths:
            files.append(("<stdin>" if p == "-" else p, read_text(p)))
    except (OSError, DocxError) as exc:
        print("fiction-slop-lint: %s" % exc, file=sys.stderr)
        return 2
    report = analyze_files(files, rules=rules, disable=disable, only_categories=cats, min_severity=args.min_severity)
    sev = report["summary"]["by_severity"]
    thresholds = None
    passed = None
    if args.strict:
        thresholds = {"max_errors": args.max_errors, "max_warnings": args.max_warnings, "max_per_1000": args.max_per_1000}
        passed = (sev["error"] <= args.max_errors and sev["warn"] <= args.max_warnings
                  and report["summary"]["warn_and_error_per_1000_words"] <= args.max_per_1000)
    if args.json:
        sys.stdout.write(render_json(report, thresholds, passed))
    else:
        sys.stdout.write(render_text(report, args.verbose, thresholds, passed))
    if args.strict and not passed:
        return 1
    return 0
