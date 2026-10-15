"""Analysis engine. Standard library only.

The algorithms here are mirrored in docs/slop.js (the browser version). If you
change one, change the other; tests/test_js_parity.py compares them when Node
is available.
"""

import bisect
import math
import re

from . import __version__
from .rules import load_rules

_TRANSLATE = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u00a0": " ", "\ufeff": " ",
})

WORD_RE = re.compile(r"[A-Za-z\u00C0-\u024F0-9]+(?:'[A-Za-z\u00C0-\u024F0-9]+)*")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
CHAPTER_RE = re.compile(
    r"^\s*(?:(?:chapter|part|book)\s+(?:\d{1,3}|[ivxlc]{1,6}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b[^\n]{0,60}|(?:prologue|epilogue|interlude))\s*$",
    re.I)
BREAK_RE = re.compile(r"^\s*(?:[-*_~=#]\s*){3,}$")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
TAG_RE = re.compile(r"<[^>]*>")
LINKURL_RE = re.compile(r"\]\([^)]*\)")
EMPH_RE = re.compile(r"[*`]|\b_|_\b")
ALPHA_RE = re.compile(r"[A-Za-z\u00C0-\u024F]")
SENT_START_RE = re.compile(r"[A-Z\u00C0-\u00DE0-9\"'(\[]")
ABBREV = frozenset("mr mrs ms dr st jr sr prof vs etc eg ie mt gen col capt lt sgt no".split())
SEV_RANK = {"info": 0, "warn": 1, "error": 2}


def _blank(m):
    return " " * len(m.group(0))


def prepare(raw):
    """Normalize text and mask non-prose (headings, code, comments, rules).

    Returns (prose, chapters). ``prose`` has exactly the same length and line
    structure as the normalized input so offsets map back to line/column.
    ``chapters`` is a list of dicts {title, offset} in order.
    """
    text = raw.replace("\r\n", "\n").replace("\r", "\n").translate(_TRANSLATE)
    lines = text.split("\n")
    out = []
    chapters = []
    offset = 0
    in_fence = False
    in_comment = False
    front_end = 0  # index of the closing line of YAML front matter, 0 if none
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                front_end = j
                break
    for idx, line in enumerate(lines):
        masked = line
        if idx <= front_end and front_end > 0:
            masked = " " * len(line)
        elif in_fence:
            masked = " " * len(line)
            if FENCE_RE.match(line):
                in_fence = False
        elif FENCE_RE.match(line):
            in_fence = True
            masked = " " * len(line)
        elif in_comment:
            masked = " " * len(line)
            if "-->" in line:
                in_comment = False
        elif "<!--" in line and "-->" not in line:
            in_comment = True
            masked = " " * len(line)
        else:
            m = HEADING_RE.match(line)
            if m:
                chapters.append({"title": m.group(1).strip(), "offset": offset})
                masked = " " * len(line)
            elif CHAPTER_RE.match(line):
                chapters.append({"title": line.strip(), "offset": offset})
                masked = " " * len(line)
            elif BREAK_RE.match(line):
                masked = " " * len(line)
            else:
                masked = TAG_RE.sub(_blank, masked)
                masked = LINKURL_RE.sub(_blank, masked)
                if masked.lstrip().startswith(">"):
                    k = masked.index(">")
                    masked = masked[:k] + " " + masked[k + 1:]
                masked = EMPH_RE.sub(" ", masked)
        out.append(masked)
        offset += len(line) + 1
    return "\n".join(out), chapters


def _paragraphs(prose):
    paras = []
    offset = 0
    cur_start = None
    cur_end = None
    for line in prose.split("\n"):
        if line.strip():
            if cur_start is None:
                cur_start = offset + (len(line) - len(line.lstrip()))
            cur_end = offset + len(line.rstrip())
        elif cur_start is not None:
            paras.append((cur_start, cur_end))
            cur_start = None
        offset += len(line) + 1
    if cur_start is not None:
        paras.append((cur_start, cur_end))
    return paras


def _is_abbrev(text, i):
    j = i
    while j > 0 and ALPHA_RE.match(text[j - 1]):
        j -= 1
    word = text[j:i]
    if not word or text[i] != ".":
        return False
    if word.lower() in ABBREV:
        return True
    if len(word) == 1 and word != "I" and "A" <= word <= "Z":
        return True
    return False


def _split_sentences(text, base):
    sents = []
    n = len(text)
    i = 0
    while i < n and text[i].isspace():
        i += 1
    start = i
    while i < n:
        c = text[i]
        if c in ".!?\u2026":
            j = i + 1
            while j < n and text[j] in ".!?\u2026":
                j += 1
            while j < n and text[j] in "\"')]":
                j += 1
            k = j
            while k < n and text[k].isspace():
                k += 1
            if k >= n:
                break
            if k > j and SENT_START_RE.match(text[k]) and not _is_abbrev(text, i):
                sents.append((base + start, base + j))
                start = k
                i = k
                continue
            i = j
            continue
        i += 1
    end = n
    while end > start and text[end - 1].isspace():
        end -= 1
    if end > start:
        sents.append((base + start, base + end))
    return sents


class Doc:
    """A prepared document with tokens, sentences, paragraphs and chapters."""

    def __init__(self, path, raw):
        self.path = path
        self.text = raw.replace("\r\n", "\n").replace("\r", "\n").translate(_TRANSLATE)
        self.prose, self.chapters = prepare(raw)
        self.line_starts = [0]
        for m in re.finditer("\n", self.text):
            self.line_starts.append(m.end())
        self.tokens = [(m.group(0), m.start()) for m in WORD_RE.finditer(self.prose)]
        self.token_starts = [t[1] for t in self.tokens]
        self.word_count = len(self.tokens)
        self.paragraphs = []  # dicts: start,end,sentences(list of sentence idx),words
        self.sentences = []   # dicts: start,end,para,first,words (token index range)
        for pi, (ps, pe) in enumerate(_paragraphs(self.prose)):
            sidx = []
            for (ss, se) in _split_sentences(self.prose[ps:pe], ps):
                first = bisect.bisect_left(self.token_starts, ss)
                last = bisect.bisect_left(self.token_starts, se)
                self.sentences.append({"start": ss, "end": se, "para": pi, "first": first, "last": last,
                                       "words": last - first})
                sidx.append(len(self.sentences) - 1)
            first = bisect.bisect_left(self.token_starts, ps)
            last = bisect.bisect_left(self.token_starts, pe)
            self.paragraphs.append({"start": ps, "end": pe, "sentences": sidx, "words": last - first,
                                    "dialogue": self.prose[ps] == '"'})
        self.chapter_offsets = [c["offset"] for c in self.chapters]

    def line_col(self, offset):
        i = bisect.bisect_right(self.line_starts, offset) - 1
        return i + 1, offset - self.line_starts[i] + 1

    def chapter_index(self, offset):
        return bisect.bisect_right(self.chapter_offsets, offset)  # 0 = before first heading

    def context(self, start, end):
        s = max(0, start - 30)
        e = min(len(self.prose), end + 30)
        return re.sub(r"\s+", " ", self.prose[s:e]).strip()

    def first_token(self, sent):
        if sent["words"] <= 0:
            return None
        return self.tokens[sent["first"]][0]


def _finding(doc, rule, offset, end=None, **extra):
    f = {
        "rule": rule["id"],
        "category": rule["category"],
        "severity": rule["severity"],
        "message": rule["message"],
        "file": doc.path,
        "line": None,
        "column": None,
        "offset": offset,
        "end": end,
        "match": None,
        "context": None,
    }
    if rule.get("suggestion"):
        f["suggestion"] = rule["suggestion"]
    if offset is not None:
        f["line"], f["column"] = doc.line_col(offset)
        if end is not None:
            f["match"] = re.sub(r"\s+", " ", doc.prose[offset:end]).strip()
            f["context"] = doc.context(offset, end)
    f.update(extra)
    return f


def _compile(rule):
    flags = 0 if rule.get("case_sensitive") else re.I
    return [re.compile(p, flags) for p in rule["patterns"]]


def _matches(doc, rule, compiled):
    """All non-overlapping matches (start, end, matched_text) for a pattern/density rule."""
    found = []
    excl = set(e.lower() for e in rule.get("exclude", []))
    for rx in compiled:
        for m in rx.finditer(doc.prose):
            if m.re.groups >= 1 and m.group(1) is not None:
                s, e = m.start(1), m.end(1)
            else:
                s, e = m.start(), m.end()
            if e <= s:
                continue
            txt = re.sub(r"\s+", " ", doc.prose[s:e]).lower()
            if txt in excl:
                continue
            found.append((s, e, txt))
    found.sort(key=lambda t: (t[0], -(t[1])))
    kept = []
    last_end = -1
    for s, e, t in found:
        if s < last_end:
            continue
        kept.append((s, e, t))
        last_end = e
    return kept


def _round(x, nd=2):
    return round(x, nd)


def _mean_cv(values):
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) * (v - mean) for v in values) / n
    sd = math.sqrt(var)
    return mean, (sd / mean if mean > 0 else 0.0)


# ----------------------------------------------------------------- metrics

def _m_repeated_openers(doc, rule, p):
    out = []
    run = p["run"]
    for para in doc.paragraphs:
        sids = para["sentences"]
        i = 0
        while i < len(sids):
            w = doc.first_token(doc.sentences[sids[i]])
            if w is None:
                i += 1
                continue
            j = i + 1
            while j < len(sids):
                w2 = doc.first_token(doc.sentences[sids[j]])
                if w2 is None or w2.lower() != w.lower():
                    break
                j += 1
            if j - i >= run:
                s = doc.sentences[sids[i]]
                out.append(_finding(doc, rule, s["start"], s["start"] + len(w), count=j - i,
                                    detail="%d sentences in a row start with '%s'" % (j - i, w)))
            i = j
    return out


def _m_opener_share(doc, rule, p):
    counts = {}
    total = 0
    first_pos = {}
    for s in doc.sentences:
        w = doc.first_token(s)
        if w is None:
            continue
        k = w.lower()
        total += 1
        if k not in counts:
            counts[k] = 0
            first_pos[k] = s["start"]
        counts[k] += 1
    if total < p["min_sentences"]:
        return []
    top = None
    for k, c in counts.items():
        if top is None or c > counts[top]:
            top = k
    share = counts[top] / total
    if share > p["max_share"]:
        return [_finding(doc, rule, first_pos[top], first_pos[top] + len(top), count=counts[top],
                         rate=_round(share * 100, 1), limit=p["max_share"] * 100,
                         detail="'%s' opens %d of %d sentences (%.0f%%)" % (top, counts[top], total, share * 100))]
    return []


def _m_sentence_length_monotony(doc, rule, p):
    sents = [s for s in doc.sentences if s["words"] > 0]
    out = []
    w = p["window"]
    i = 0
    while i + w <= len(sents):
        vals = [s["words"] for s in sents[i:i + w]]
        mean, cv = _mean_cv(vals)
        if mean >= p["min_mean"] and cv < p["max_cv"]:
            out.append(_finding(doc, rule, sents[i]["start"], sents[i]["start"] + 1, count=w,
                                detail="%d sentences averaging %.1f words with little variation (cv %.2f)" % (w, mean, cv)))
            i += w
        else:
            i += 1
    return out


def _m_paragraph_length_monotony(doc, rule, p):
    paras = [q for q in doc.paragraphs if q["words"] > 0]
    out = []
    w = p["window"]
    i = 0
    while i + w <= len(paras):
        vals = [q["words"] for q in paras[i:i + w]]
        mean, cv = _mean_cv(vals)
        if mean >= p["min_mean"] and cv < p["max_cv"]:
            out.append(_finding(doc, rule, paras[i]["start"], paras[i]["start"] + 1, count=w,
                                detail="%d paragraphs averaging %.1f words with little variation (cv %.2f)" % (w, mean, cv)))
            i += w
        else:
            i += 1
    return out


def _m_short_sentence_streak(doc, rule, p):
    out = []
    for para in doc.paragraphs:
        sids = para["sentences"]
        i = 0
        while i < len(sids):
            def short(k):
                n = doc.sentences[sids[k]]["words"]
                return 1 <= n <= p["max_words"]
            if not short(i):
                i += 1
                continue
            j = i
            while j < len(sids) and short(j):
                j += 1
            if j - i >= p["run"]:
                s = doc.sentences[sids[i]]
                out.append(_finding(doc, rule, s["start"], s["start"] + 1, count=j - i,
                                    detail="%d very short sentences in a row" % (j - i)))
            i = j
    return out


def _m_long_sentence(doc, rule, p):
    out = []
    for s in doc.sentences:
        if s["words"] > p["max_words"]:
            out.append(_finding(doc, rule, s["start"], s["start"] + 1, count=s["words"],
                                detail="sentence of %d words" % s["words"]))
    return out


def _m_single_sentence_paragraph_share(doc, rule, p):
    narr = [q for q in doc.paragraphs if q["words"] > 0 and not q["dialogue"]]
    if len(narr) < p["min_paragraphs"]:
        return []
    singles = [q for q in narr if len(q["sentences"]) == 1]
    share = len(singles) / len(narr)
    if share > p["max_share"]:
        return [_finding(doc, rule, singles[0]["start"], singles[0]["start"] + 1, count=len(singles),
                         rate=_round(share * 100, 1), limit=p["max_share"] * 100,
                         detail="%d of %d narrative paragraphs are one sentence (%.0f%%)" % (len(singles), len(narr), share * 100))]
    return []


def _m_punchline_endings(doc, rule, p):
    elig = [q for q in doc.paragraphs if q["words"] > 0 and not q["dialogue"] and len(q["sentences"]) >= 2]
    if len(elig) < p["min_paragraphs"]:
        return []
    punch = []
    for q in elig:
        last = doc.sentences[q["sentences"][-1]]
        prev = doc.sentences[q["sentences"][-2]]
        if 1 <= last["words"] <= p["max_tail_words"] and prev["words"] >= p["min_prior_words"]:
            punch.append(q)
    share = len(punch) / len(elig)
    if punch and share > p["max_share"]:
        last = doc.sentences[punch[0]["sentences"][-1]]
        return [_finding(doc, rule, last["start"], last["end"], count=len(punch),
                         rate=_round(share * 100, 1), limit=p["max_share"] * 100,
                         detail="%d of %d multi-sentence paragraphs end on a very short sentence (%.0f%%)" % (len(punch), len(elig), share * 100))]
    return []


def _m_name_frequency(doc, rule, p, stop):
    if doc.word_count < p["min_words"]:
        return []
    ignore = set(p.get("ignore", []))
    initial = set()
    for s in doc.sentences:
        if s["words"] > 0:
            initial.add(s["first"])
    stats = {}
    for ti, (tok, pos) in enumerate(doc.tokens):
        if not ("A" <= tok[0] <= "Z"):
            if "a" <= tok[0] <= "z":
                key = tok.lower()
                if key.endswith("'s"):
                    key = key[:-2]
                st = stats.setdefault(key, {"total": 0, "mid": 0, "lower": 0, "first": pos})
                st["lower"] += 1
            continue
        if tok == "I" or tok.startswith("I'"):
            continue
        if len(tok) >= 2 and tok == tok.upper():
            continue
        key = tok.lower()
        if key.endswith("'s"):
            key = key[:-2]
        if key not in stats:
            stats[key] = {"total": 0, "mid": 0, "lower": 0, "first": pos}
        st = stats[key]
        st["total"] += 1
        if ti not in initial:
            st["mid"] += 1
    cands = []
    for key, st in stats.items():
        if key in ignore or key in stop:
            continue
        if st["mid"] >= 3 and st["lower"] == 0 and st["total"] >= p["min_mentions"]:
            rate = st["total"] * 1000.0 / doc.word_count
            if rate > p["max_per_1000"]:
                cands.append((key, st, rate))
    cands.sort(key=lambda c: -c[2])
    out = []
    for key, st, rate in cands[: p["max_report"]]:
        out.append(_finding(doc, rule, st["first"], st["first"] + len(key), count=st["total"], rate=_round(rate, 1),
                            limit=p["max_per_1000"],
                            detail="'%s' appears %d times (%.1f per 1000 words)" % (key, st["total"], rate)))
    return out


def _m_echo_words(doc, rule, p, stop):
    pos = {}
    for ti, (tok, off) in enumerate(doc.tokens):
        if len(tok) < p["min_len"] or not ("a" <= tok[0] <= "z") or tok.lower() in stop:
            continue
        pos.setdefault(tok.lower(), []).append(ti)
    hits = []
    for w, lst in pos.items():
        i = 0
        r = p["repeats"]
        while i + r - 1 < len(lst):
            if lst[i + r - 1] - lst[i] < p["window"]:
                hits.append((doc.tokens[lst[i]][1], w, r))
                i += r
            else:
                i += 1
    hits.sort(key=lambda h: h[0])
    out = []
    for off, w, r in hits[: p["max_report"]]:
        out.append(_finding(doc, rule, off, off + len(w), count=r,
                            detail="'%s' used %d times within %d words" % (w, r, p["window"])))
    return out


_DOC_METRICS = {
    "repeated_openers": _m_repeated_openers,
    "opener_share": _m_opener_share,
    "sentence_length_monotony": _m_sentence_length_monotony,
    "paragraph_length_monotony": _m_paragraph_length_monotony,
    "short_sentence_streak": _m_short_sentence_streak,
    "long_sentence": _m_long_sentence,
    "single_sentence_paragraph_share": _m_single_sentence_paragraph_share,
    "punchline_endings": _m_punchline_endings,
}


def ngram_repeat(docs, rule, stop):
    """Corpus level repeated phrases. Returns findings (with file/line of first use)."""
    p = rule["params"]
    n = p["n"]
    counts = {}
    chap = {}
    first = {}
    locs = {}
    for fi, doc in enumerate(docs):
        for s in doc.sentences:
            toks = [doc.tokens[k][0].lower() for k in range(s["first"], s["last"])]
            for k in range(len(toks) - n + 1):
                g = tuple(toks[k:k + n])
                content = 0
                for w in g:
                    if w not in stop:
                        content += 1
                if content < p["min_content_words"]:
                    continue
                off = doc.tokens[s["first"] + k][1]
                if g not in counts:
                    counts[g] = 0
                    chap[g] = set()
                    first[g] = (fi, off)
                    locs[g] = []
                counts[g] += 1
                chap[g].add((fi, doc.chapter_index(off)))
                if len(locs[g]) < 5:
                    locs[g].append((fi, off))
    flagged = [g for g in counts if counts[g] >= p["min_total"] or len(chap[g]) >= p["min_chapters"]]
    flagged.sort(key=lambda g: first[g])
    phrases = []
    tails = {}
    for g in flagged:
        key = (counts[g], len(chap[g]), g[:-1])
        ph = tails.pop(key, None)
        if ph is not None:
            ph["words"].append(g[-1])
            tails[(ph["count"], ph["chapters"], tuple(ph["words"][-(n - 1):]))] = ph
        else:
            ph = {"words": list(g), "count": counts[g], "chapters": len(chap[g]), "first": first[g], "locs": locs[g]}
            phrases.append(ph)
            tails[(ph["count"], ph["chapters"], tuple(ph["words"][-(n - 1):]))] = ph
    phrases.sort(key=lambda ph: (-ph["count"], ph["first"]))
    out = []
    for ph in phrases[: p["max_report"]]:
        fi, off = ph["first"]
        doc = docs[fi]
        text = " ".join(ph["words"])
        f = _finding(doc, rule, off, off + len(text), count=ph["count"], scope="corpus",
                     detail="'%s' appears %d times in %d chapter(s)" % (text, ph["count"], ph["chapters"]),
                     phrase=text,
                     locations=[{"file": docs[a].path, "line": docs[a].line_col(b)[0]} for a, b in ph["locs"]])
        out.append(f)
    return out


# --------------------------------------------------------------- orchestration

def _wanted(rule, disable, only_categories, min_severity):
    if rule["id"] in disable:
        return False
    if only_categories and rule["category"] not in only_categories:
        return False
    return SEV_RANK[rule["severity"]] >= SEV_RANK[min_severity]


def analyze_files(files, rules=None, disable=(), only_categories=(), min_severity="info"):
    """Analyze a list of (path, text) pairs. Returns a report dict."""
    if rules is None:
        rules = load_rules()
    stop = set(rules.get("stopwords", []))
    disable = set(disable)
    only_categories = set(only_categories)
    active = [r for r in rules["rules"] if _wanted(r, disable, only_categories, min_severity)]
    docs = [Doc(path, text) for path, text in files]
    compiled = {r["id"]: _compile(r) for r in active if r["type"] in ("pattern", "density")}
    file_reports = []
    for doc in docs:
        findings = []
        for r in active:
            t = r["type"]
            if t == "pattern":
                for s, e, _txt in _matches(doc, r, compiled[r["id"]]):
                    findings.append(_finding(doc, r, s, e))
            elif t == "density":
                if doc.word_count < r.get("min_words", 0):
                    continue
                ms = _matches(doc, r, compiled[r["id"]])
                if not ms:
                    continue
                rate = len(ms) * 1000.0 / doc.word_count
                if len(ms) >= r["min_count"] and rate > r["max_per_1000"]:
                    lines = []
                    for s, _e, _t in ms:
                        ln = doc.line_col(s)[0]
                        if ln not in lines:
                            lines.append(ln)
                    findings.append(_finding(
                        doc, r, ms[0][0], ms[0][1], count=len(ms), rate=_round(rate, 1), limit=r["max_per_1000"],
                        lines=lines[:8], scope="document",
                        detail="%d occurrences, %.1f per 1000 words (limit %s)" % (len(ms), rate, r["max_per_1000"])))
            elif t == "metric":
                m = r["metric"]
                if m in _DOC_METRICS:
                    findings.extend(_DOC_METRICS[m](doc, r, r["params"]))
                elif m == "name_frequency":
                    findings.extend(_m_name_frequency(doc, r, r["params"], stop))
                elif m == "echo_words":
                    findings.extend(_m_echo_words(doc, r, r["params"], stop))
        findings.sort(key=lambda f: (f["offset"] if f["offset"] is not None else -1, f["rule"]))
        file_reports.append({
            "path": doc.path,
            "words": doc.word_count,
            "sentences": len(doc.sentences),
            "paragraphs": len(doc.paragraphs),
            "chapters": [c["title"] for c in doc.chapters],
            "findings": findings,
        })
    corpus = []
    for r in active:
        if r["type"] == "metric" and r["metric"] == "ngram_repeat" and docs:
            corpus.extend(ngram_repeat(docs, r, stop))
    return _summarize(file_reports, corpus, rules)


def _summarize(file_reports, corpus, rules):
    allf = [f for fr in file_reports for f in fr["findings"]] + corpus
    by_sev = {"error": 0, "warn": 0, "info": 0}
    by_cat = {}
    for f in allf:
        by_sev[f["severity"]] += 1
        by_cat[f["category"]] = by_cat.get(f["category"], 0) + 1
    words = sum(fr["words"] for fr in file_reports)
    scored = by_sev["error"] + by_sev["warn"]
    return {
        "tool": "fiction-slop-lint",
        "version": __version__,
        "disclaimer": "Style linter only. Findings are hints, not proof of how a text was written.",
        "files": file_reports,
        "corpus": corpus,
        "summary": {
            "files": len(file_reports),
            "words": words,
            "findings": len(allf),
            "by_severity": by_sev,
            "by_category": dict(sorted(by_cat.items())),
            "warn_and_error_per_1000_words": round(scored * 1000.0 / words, 2) if words else 0.0,
        },
    }


def analyze(text, path="<text>", **kw):
    """Convenience wrapper for a single string."""
    return analyze_files([(path, text)], **kw)
