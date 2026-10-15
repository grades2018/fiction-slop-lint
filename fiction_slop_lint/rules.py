"""Loading and validating the JSON rules file."""

import json
import re
from importlib import resources

SEVERITIES = ("info", "warn", "error")
RULE_TYPES = ("pattern", "density", "metric")
METRICS = (
    "repeated_openers",
    "opener_share",
    "ngram_repeat",
    "name_frequency",
    "echo_words",
    "sentence_length_monotony",
    "paragraph_length_monotony",
    "short_sentence_streak",
    "long_sentence",
    "single_sentence_paragraph_share",
    "punchline_endings",
)


class RulesError(ValueError):
    pass


def default_rules_text():
    return resources.files("fiction_slop_lint").joinpath("data/rules.json").read_text(encoding="utf-8")


def load_rules(path=None):
    """Load rules from ``path`` or the bundled rules.json. Returns a validated dict."""
    if path is None:
        text = default_rules_text()
        source = "built-in"
    else:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        source = str(path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RulesError("%s: invalid JSON: %s" % (source, exc)) from exc
    validate_rules(data, source)
    return data


def validate_rules(data, source="rules"):
    if not isinstance(data, dict) or not isinstance(data.get("rules"), list):
        raise RulesError("%s: top level must be an object with a 'rules' list" % source)
    seen = set()
    cats = data.get("categories", {})
    for i, rule in enumerate(data["rules"]):
        where = "%s: rule #%d" % (source, i + 1)
        if not isinstance(rule, dict):
            raise RulesError(where + " is not an object")
        rid = rule.get("id")
        if not isinstance(rid, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", rid):
            raise RulesError(where + ": bad or missing id")
        where = "%s: rule '%s'" % (source, rid)
        if rid in seen:
            raise RulesError(where + ": duplicate id")
        seen.add(rid)
        if rule.get("severity") not in SEVERITIES:
            raise RulesError(where + ": severity must be one of %s" % (SEVERITIES,))
        if rule.get("type") not in RULE_TYPES:
            raise RulesError(where + ": type must be one of %s" % (RULE_TYPES,))
        if not isinstance(rule.get("message"), str) or not rule["message"]:
            raise RulesError(where + ": missing message")
        if cats and rule.get("category") not in cats:
            raise RulesError(where + ": category '%s' not declared in 'categories'" % rule.get("category"))
        if rule["type"] in ("pattern", "density"):
            pats = rule.get("patterns")
            if not isinstance(pats, list) or not pats:
                raise RulesError(where + ": needs a non-empty 'patterns' list")
            for p in pats:
                try:
                    re.compile(p)
                except re.error as exc:
                    raise RulesError("%s: bad regex %r: %s" % (where, p, exc)) from exc
        if rule["type"] == "density":
            for key in ("max_per_1000", "min_count"):
                if not isinstance(rule.get(key), (int, float)):
                    raise RulesError(where + ": density rules need numeric '%s'" % key)
        if rule["type"] == "metric":
            if rule.get("metric") not in METRICS:
                raise RulesError(where + ": unknown metric %r" % rule.get("metric"))
            if not isinstance(rule.get("params"), dict):
                raise RulesError(where + ": metric rules need 'params'")
