"""Plain text and JSON report rendering."""

import json

HEADER = "fiction-slop-lint %s - a style linter for fiction. Not an AI detector."


def render_json(report, thresholds=None, passed=None):
    out = dict(report)
    if thresholds is not None:
        out["strict"] = {"thresholds": thresholds, "passed": passed}
    return json.dumps(out, indent=2, ensure_ascii=False) + "\n"


def _loc(f):
    if f["line"] is None:
        return "(file)"
    return "%d:%d" % (f["line"], f["column"])


def _one(f, verbose):
    lines = []
    head = "  %-8s %-5s %-34s %s" % (_loc(f), f["severity"], f["rule"], f.get("detail") or f["message"])
    lines.append(head)
    if f.get("detail"):
        lines.append("  %s%s" % (" " * 49, f["message"]))
    if f.get("match") and not f.get("detail"):
        lines.append("  %s> %s" % (" " * 49, f["context"] if verbose else f["match"]))
    elif f.get("match") and verbose:
        lines.append("  %s> %s" % (" " * 49, f["context"]))
    if f.get("lines"):
        more = ", ".join(str(n) for n in f["lines"])
        lines.append("  %slines: %s" % (" " * 49, more))
    if verbose and f.get("suggestion"):
        lines.append("  %stip: %s" % (" " * 49, f["suggestion"]))
    return lines


def render_text(report, verbose=False, thresholds=None, passed=None):
    out = [HEADER % report["version"], ""]
    for fr in report["files"]:
        out.append("%s  (%d words, %d sentences, %d findings)" % (fr["path"], fr["words"], fr["sentences"], len(fr["findings"])))
        if not fr["findings"]:
            out.append("  no findings")
        for f in fr["findings"]:
            out.extend(_one(f, verbose))
        out.append("")
    if report["corpus"]:
        out.append("Repeated phrases across the whole input")
        for f in report["corpus"]:
            locs = ", ".join("%s:%d" % (l["file"], l["line"]) for l in f["locations"][:3])
            out.append("  %-5s %-34s %s" % (f["severity"], f["rule"], f["detail"]))
            out.append("  %sfirst at %s" % (" " * 41, locs))
        out.append("")
    s = report["summary"]
    sev = s["by_severity"]
    out.append("Summary")
    out.append("  %d file(s), %d words, %d findings" % (s["files"], s["words"], s["findings"]))
    out.append("  errors %d, warnings %d, info %d" % (sev["error"], sev["warn"], sev["info"]))
    out.append("  warnings+errors per 1000 words: %.1f" % s["warn_and_error_per_1000_words"])
    if s["by_category"]:
        out.append("  by category: " + ", ".join("%s %d" % (k, v) for k, v in s["by_category"].items()))
    if thresholds is not None:
        out.append("  strict: %s (max errors %s, max warnings %s, max per 1000 %s)" % (
            "PASS" if passed else "FAIL", thresholds["max_errors"], thresholds["max_warnings"], thresholds["max_per_1000"]))
    out.append("")
    out.append("Findings are style hints, not proof of how a text was written. Expect false positives.")
    return "\n".join(out) + "\n"


def render_rules_text(rules):
    out = []
    for r in rules["rules"]:
        out.append("%-34s %-14s %-5s %-8s %s" % (r["id"], r["category"], r["severity"], r["type"], r["message"]))
    out.append("")
    out.append("%d rules" % len(rules["rules"]))
    return "\n".join(out) + "\n"


def render_rules_markdown(rules):
    cats = rules.get("categories", {})
    out = ["| Rule id | Category | Severity | Type | What it flags |", "|---|---|---|---|---|"]
    for r in rules["rules"]:
        out.append("| `%s` | %s | %s | %s | %s |" % (r["id"], r["category"], r["severity"], r["type"], r["message"].replace("|", "/")))
    out.append("")
    out.append("%d rules in %d categories." % (len(rules["rules"]), len(cats)))
    return "\n".join(out) + "\n"
