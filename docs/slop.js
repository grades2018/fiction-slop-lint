/*
 * fiction-slop-lint, browser/Node engine.
 * Mirrors fiction_slop_lint/engine.py and uses the same rules.json.
 * No dependencies, no network access. If you change an algorithm here, change it
 * in the Python engine too (tests/test_js_parity.py compares them).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.SlopLint = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var VERSION = "0.1.1";
  var TRANSLATE = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u2032": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u00a0": " ", "\ufeff": " "
  };
  var TRANSLATE_RE = /[\u2018\u2019\u201a\u2032\u201c\u201d\u201e\u00a0\ufeff]/g;
  var WORD_RE_SRC = "[A-Za-z\\u00C0-\\u024F0-9]+(?:'[A-Za-z\\u00C0-\\u024F0-9]+)*";
  var HEADING_RE = /^\s{0,3}#{1,6}\s+(.*)$/;
  var CHAPTER_RE = /^\s*(?:(?:chapter|part|book)\s+(?:\d{1,3}|[ivxlc]{1,6}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\b[^\n]{0,60}|(?:prologue|epilogue|interlude))\s*$/i;
  var BREAK_RE = /^\s*(?:[-*_~=#]\s*){3,}$/;
  var FENCE_RE = /^\s*(?:```|~~~)/;
  var TAG_RE = /<[^>]*>/g;
  var LINKURL_RE = /\]\([^)]*\)/g;
  var EMPH_RE = /[*`]|\b_|_\b/g;
  var SENT_START_RE = /^[A-Z\u00C0-\u00DE0-9"'(\[]/;
  var ALPHA_RE = /^[A-Za-z\u00C0-\u024F]$/;
  var ABBREV = {};
  "mr mrs ms dr st jr sr prof vs etc eg ie mt gen col capt lt sgt no".split(" ").forEach(function (w) { ABBREV[w] = true; });
  var SEV_RANK = { info: 0, warn: 1, error: 2 };

  function spaces(n) { return new Array(n + 1).join(" "); }
  function blank(m) { return spaces(m.length); }
  function isSpace(c) { return /\s/.test(c); }
  function collapse(s) { return s.replace(/\s+/g, " ").trim(); }
  function round(x, nd) { var f = Math.pow(10, nd); return Math.round(x * f) / f; }

  function normalize(raw) {
    return raw.replace(/\r\n/g, "\n").replace(/\r/g, "\n").replace(TRANSLATE_RE, function (c) { return TRANSLATE[c]; });
  }

  function prepare(raw) {
    var text = normalize(raw);
    var lines = text.split("\n");
    var out = [], chapters = [], offset = 0, inFence = false, inComment = false, frontEnd = 0;
    if (lines.length && lines[0].trim() === "---") {
      for (var j = 1; j < lines.length; j++) {
        var t = lines[j].trim();
        if (t === "---" || t === "...") { frontEnd = j; break; }
      }
    }
    for (var idx = 0; idx < lines.length; idx++) {
      var line = lines[idx], masked = line, m;
      if (idx <= frontEnd && frontEnd > 0) {
        masked = spaces(line.length);
      } else if (inFence) {
        masked = spaces(line.length);
        if (FENCE_RE.test(line)) inFence = false;
      } else if (FENCE_RE.test(line)) {
        inFence = true; masked = spaces(line.length);
      } else if (inComment) {
        masked = spaces(line.length);
        if (line.indexOf("-->") >= 0) inComment = false;
      } else if (line.indexOf("<!--") >= 0 && line.indexOf("-->") < 0) {
        inComment = true; masked = spaces(line.length);
      } else {
        m = HEADING_RE.exec(line);
        if (m) {
          chapters.push({ title: m[1].trim(), offset: offset });
          masked = spaces(line.length);
        } else if (CHAPTER_RE.test(line)) {
          chapters.push({ title: line.trim(), offset: offset });
          masked = spaces(line.length);
        } else if (BREAK_RE.test(line)) {
          masked = spaces(line.length);
        } else {
          masked = masked.replace(TAG_RE, blank).replace(LINKURL_RE, blank);
          if (masked.replace(/^\s+/, "").charAt(0) === ">") {
            var k = masked.indexOf(">");
            masked = masked.slice(0, k) + " " + masked.slice(k + 1);
          }
          masked = masked.replace(EMPH_RE, " ");
        }
      }
      out.push(masked);
      offset += line.length + 1;
    }
    return { text: text, prose: out.join("\n"), chapters: chapters };
  }

  function bisectLeft(arr, x) {
    var lo = 0, hi = arr.length;
    while (lo < hi) { var mid = (lo + hi) >> 1; if (arr[mid] < x) lo = mid + 1; else hi = mid; }
    return lo;
  }
  function bisectRight(arr, x) {
    var lo = 0, hi = arr.length;
    while (lo < hi) { var mid = (lo + hi) >> 1; if (x < arr[mid]) hi = mid; else lo = mid + 1; }
    return lo;
  }

  function paragraphsOf(prose) {
    var paras = [], offset = 0, curStart = null, curEnd = null, lines = prose.split("\n");
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      if (line.trim()) {
        if (curStart === null) curStart = offset + (line.length - line.replace(/^\s+/, "").length);
        curEnd = offset + line.replace(/\s+$/, "").length;
      } else if (curStart !== null) {
        paras.push([curStart, curEnd]); curStart = null;
      }
      offset += line.length + 1;
    }
    if (curStart !== null) paras.push([curStart, curEnd]);
    return paras;
  }

  function isAbbrev(text, i) {
    var j = i;
    while (j > 0 && ALPHA_RE.test(text.charAt(j - 1))) j--;
    var word = text.slice(j, i);
    if (!word || text.charAt(i) !== ".") return false;
    if (ABBREV[word.toLowerCase()] === true) return true;
    if (word.length === 1 && word !== "I" && word >= "A" && word <= "Z") return true;
    return false;
  }

  function splitSentences(text, base) {
    var sents = [], n = text.length, i = 0;
    while (i < n && isSpace(text.charAt(i))) i++;
    var start = i;
    while (i < n) {
      var c = text.charAt(i);
      if (".!?\u2026".indexOf(c) >= 0) {
        var j = i + 1;
        while (j < n && ".!?\u2026".indexOf(text.charAt(j)) >= 0) j++;
        while (j < n && "\"')]".indexOf(text.charAt(j)) >= 0) j++;
        var k = j;
        while (k < n && isSpace(text.charAt(k))) k++;
        if (k >= n) break;
        if (k > j && SENT_START_RE.test(text.charAt(k)) && !isAbbrev(text, i)) {
          sents.push([base + start, base + j]);
          start = k; i = k; continue;
        }
        i = j; continue;
      }
      i++;
    }
    var end = n;
    while (end > start && isSpace(text.charAt(end - 1))) end--;
    if (end > start) sents.push([base + start, base + end]);
    return sents;
  }

  function Doc(path, raw) {
    var prep = prepare(raw);
    this.path = path;
    this.text = prep.text;
    this.prose = prep.prose;
    this.chapters = prep.chapters;
    this.lineStarts = [0];
    for (var i = 0; i < this.text.length; i++) if (this.text.charAt(i) === "\n") this.lineStarts.push(i + 1);
    this.tokens = [];
    var re = new RegExp(WORD_RE_SRC, "g"), m;
    while ((m = re.exec(this.prose)) !== null) this.tokens.push([m[0], m.index]);
    this.tokenStarts = this.tokens.map(function (t) { return t[1]; });
    this.wordCount = this.tokens.length;
    this.paragraphs = [];
    this.sentences = [];
    var plist = paragraphsOf(this.prose);
    for (var pi = 0; pi < plist.length; pi++) {
      var ps = plist[pi][0], pe = plist[pi][1], sidx = [];
      var ss = splitSentences(this.prose.slice(ps, pe), ps);
      for (var si = 0; si < ss.length; si++) {
        var first = bisectLeft(this.tokenStarts, ss[si][0]);
        var last = bisectLeft(this.tokenStarts, ss[si][1]);
        this.sentences.push({ start: ss[si][0], end: ss[si][1], para: pi, first: first, last: last, words: last - first });
        sidx.push(this.sentences.length - 1);
      }
      var f2 = bisectLeft(this.tokenStarts, ps), l2 = bisectLeft(this.tokenStarts, pe);
      this.paragraphs.push({ start: ps, end: pe, sentences: sidx, words: l2 - f2, dialogue: this.prose.charAt(ps) === '"' });
    }
    this.chapterOffsets = this.chapters.map(function (c) { return c.offset; });
  }
  Doc.prototype.lineCol = function (offset) {
    var i = bisectRight(this.lineStarts, offset) - 1;
    return [i + 1, offset - this.lineStarts[i] + 1];
  };
  Doc.prototype.chapterIndex = function (offset) { return bisectRight(this.chapterOffsets, offset); };
  Doc.prototype.context = function (s, e) {
    return collapse(this.prose.slice(Math.max(0, s - 30), Math.min(this.prose.length, e + 30)));
  };
  Doc.prototype.firstToken = function (sent) { return sent.words <= 0 ? null : this.tokens[sent.first][0]; };

  function mk(doc, rule, offset, end, extra) {
    var f = {
      rule: rule.id, category: rule.category, severity: rule.severity, message: rule.message,
      file: doc.path, line: null, column: null, offset: offset, end: (end === undefined ? null : end), match: null, context: null
    };
    if (rule.suggestion) f.suggestion = rule.suggestion;
    if (offset !== null && offset !== undefined) {
      var lc = doc.lineCol(offset);
      f.line = lc[0]; f.column = lc[1];
      if (end !== null && end !== undefined) {
        f.match = collapse(doc.prose.slice(offset, end));
        f.context = doc.context(offset, end);
      }
    }
    if (extra) for (var k in extra) f[k] = extra[k];
    return f;
  }

  function compileRule(rule) {
    var flags = "gd" + (rule.case_sensitive ? "" : "i");
    return rule.patterns.map(function (p) { return new RegExp(p, flags); });
  }

  function matchesOf(doc, rule, compiled) {
    var found = [], excl = {};
    (rule.exclude || []).forEach(function (e) { excl[e.toLowerCase()] = true; });
    compiled.forEach(function (rx) {
      rx.lastIndex = 0;
      var m;
      while ((m = rx.exec(doc.prose)) !== null) {
        var s, e;
        if (m.length > 1 && m[1] !== undefined && m.indices && m.indices[1]) { s = m.indices[1][0]; e = m.indices[1][1]; }
        else { s = m.index; e = m.index + m[0].length; }
        if (m[0].length === 0) { rx.lastIndex++; continue; }
        if (e <= s) continue;
        var txt = collapse(doc.prose.slice(s, e)).toLowerCase();
        if (excl[txt] === true) continue;
        found.push([s, e, txt]);
      }
    });
    found.sort(function (a, b) { return a[0] - b[0] || b[1] - a[1]; });
    var kept = [], lastEnd = -1;
    found.forEach(function (t) { if (t[0] >= lastEnd) { kept.push(t); lastEnd = t[1]; } });
    return kept;
  }

  function meanCv(vals) {
    var n = vals.length, sum = 0, i;
    for (i = 0; i < n; i++) sum += vals[i];
    var mean = sum / n, v = 0;
    for (i = 0; i < n; i++) v += (vals[i] - mean) * (vals[i] - mean);
    var sd = Math.sqrt(v / n);
    return [mean, mean > 0 ? sd / mean : 0];
  }
  function fx(x, d) { return Number(x).toFixed(d); }

  var METRICS = {};

  METRICS.repeated_openers = function (doc, rule, p) {
    var out = [];
    doc.paragraphs.forEach(function (para) {
      var sids = para.sentences, i = 0;
      while (i < sids.length) {
        var w = doc.firstToken(doc.sentences[sids[i]]);
        if (w === null) { i++; continue; }
        var j = i + 1;
        while (j < sids.length) {
          var w2 = doc.firstToken(doc.sentences[sids[j]]);
          if (w2 === null || w2.toLowerCase() !== w.toLowerCase()) break;
          j++;
        }
        if (j - i >= p.run) {
          var s = doc.sentences[sids[i]];
          out.push(mk(doc, rule, s.start, s.start + w.length, { count: j - i, detail: (j - i) + " sentences in a row start with '" + w + "'" }));
        }
        i = j;
      }
    });
    return out;
  };

  METRICS.opener_share = function (doc, rule, p) {
    var counts = new Map(), firstPos = new Map(), total = 0;
    doc.sentences.forEach(function (s) {
      var w = doc.firstToken(s);
      if (w === null) return;
      var k = w.toLowerCase();
      total++;
      if (!counts.has(k)) { counts.set(k, 0); firstPos.set(k, s.start); }
      counts.set(k, counts.get(k) + 1);
    });
    if (total < p.min_sentences) return [];
    var top = null;
    counts.forEach(function (c, k) { if (top === null || c > counts.get(top)) top = k; });
    var share = counts.get(top) / total;
    if (share > p.max_share) {
      return [mk(doc, rule, firstPos.get(top), firstPos.get(top) + top.length, {
        count: counts.get(top), rate: round(share * 100, 1), limit: p.max_share * 100,
        detail: "'" + top + "' opens " + counts.get(top) + " of " + total + " sentences (" + fx(share * 100, 0) + "%)"
      })];
    }
    return [];
  };

  function windowMetric(items, p, startOf, doc, rule, what) {
    var out = [], w = p.window, i = 0;
    while (i + w <= items.length) {
      var vals = items.slice(i, i + w).map(function (s) { return s.words; });
      var mc = meanCv(vals);
      if (mc[0] >= p.min_mean && mc[1] < p.max_cv) {
        var st = items[i].start;
        out.push(mk(doc, rule, st, st + 1, { count: w, detail: w + " " + what + " averaging " + fx(mc[0], 1) + " words with little variation (cv " + fx(mc[1], 2) + ")" }));
        i += w;
      } else i++;
    }
    return out;
  }
  METRICS.sentence_length_monotony = function (doc, rule, p) {
    return windowMetric(doc.sentences.filter(function (s) { return s.words > 0; }), p, null, doc, rule, "sentences");
  };
  METRICS.paragraph_length_monotony = function (doc, rule, p) {
    return windowMetric(doc.paragraphs.filter(function (q) { return q.words > 0; }), p, null, doc, rule, "paragraphs");
  };

  METRICS.short_sentence_streak = function (doc, rule, p) {
    var out = [];
    doc.paragraphs.forEach(function (para) {
      var sids = para.sentences, i = 0;
      function short(k) { var n = doc.sentences[sids[k]].words; return n >= 1 && n <= p.max_words; }
      while (i < sids.length) {
        if (!short(i)) { i++; continue; }
        var j = i;
        while (j < sids.length && short(j)) j++;
        if (j - i >= p.run) {
          var s = doc.sentences[sids[i]];
          out.push(mk(doc, rule, s.start, s.start + 1, { count: j - i, detail: (j - i) + " very short sentences in a row" }));
        }
        i = j;
      }
    });
    return out;
  };

  METRICS.long_sentence = function (doc, rule, p) {
    var out = [];
    doc.sentences.forEach(function (s) {
      if (s.words > p.max_words) out.push(mk(doc, rule, s.start, s.start + 1, { count: s.words, detail: "sentence of " + s.words + " words" }));
    });
    return out;
  };

  METRICS.single_sentence_paragraph_share = function (doc, rule, p) {
    var narr = doc.paragraphs.filter(function (q) { return q.words > 0 && !q.dialogue; });
    if (narr.length < p.min_paragraphs) return [];
    var singles = narr.filter(function (q) { return q.sentences.length === 1; });
    var share = singles.length / narr.length;
    if (share > p.max_share) {
      return [mk(doc, rule, singles[0].start, singles[0].start + 1, {
        count: singles.length, rate: round(share * 100, 1), limit: p.max_share * 100,
        detail: singles.length + " of " + narr.length + " narrative paragraphs are one sentence (" + fx(share * 100, 0) + "%)"
      })];
    }
    return [];
  };

  METRICS.punchline_endings = function (doc, rule, p) {
    var elig = doc.paragraphs.filter(function (q) { return q.words > 0 && !q.dialogue && q.sentences.length >= 2; });
    if (elig.length < p.min_paragraphs) return [];
    var punch = elig.filter(function (q) {
      var last = doc.sentences[q.sentences[q.sentences.length - 1]], prev = doc.sentences[q.sentences[q.sentences.length - 2]];
      return last.words >= 1 && last.words <= p.max_tail_words && prev.words >= p.min_prior_words;
    });
    var share = punch.length / elig.length;
    if (punch.length && share > p.max_share) {
      var last = doc.sentences[punch[0].sentences[punch[0].sentences.length - 1]];
      return [mk(doc, rule, last.start, last.end, {
        count: punch.length, rate: round(share * 100, 1), limit: p.max_share * 100,
        detail: punch.length + " of " + elig.length + " multi-sentence paragraphs end on a very short sentence (" + fx(share * 100, 0) + "%)"
      })];
    }
    return [];
  };

  METRICS.name_frequency = function (doc, rule, p, stop) {
    if (doc.wordCount < p.min_words) return [];
    var ignore = {};
    (p.ignore || []).forEach(function (w) { ignore[w] = true; });
    var initial = {};
    doc.sentences.forEach(function (s) { if (s.words > 0) initial[s.first] = true; });
    var stats = new Map();
    for (var ti = 0; ti < doc.tokens.length; ti++) {
      var tok = doc.tokens[ti][0], pos = doc.tokens[ti][1], c0 = tok.charAt(0), key, st;
      if (!(c0 >= "A" && c0 <= "Z")) {
        if (c0 >= "a" && c0 <= "z") {
          key = tok.toLowerCase();
          if (key.slice(-2) === "'s") key = key.slice(0, -2);
          if (!stats.has(key)) stats.set(key, { total: 0, mid: 0, lower: 0, first: pos });
          stats.get(key).lower++;
        }
        continue;
      }
      if (tok === "I" || tok.indexOf("I'") === 0) continue;
      if (tok.length >= 2 && tok === tok.toUpperCase()) continue;
      key = tok.toLowerCase();
      if (key.slice(-2) === "'s") key = key.slice(0, -2);
      if (!stats.has(key)) stats.set(key, { total: 0, mid: 0, lower: 0, first: pos });
      st = stats.get(key);
      st.total++;
      if (initial[ti] !== true) st.mid++;
    }
    var cands = [];
    stats.forEach(function (st, key) {
      if (ignore[key] === true || stop[key] === true) return;
      if (st.mid >= 3 && st.lower === 0 && st.total >= p.min_mentions) {
        var rate = st.total * 1000 / doc.wordCount;
        if (rate > p.max_per_1000) cands.push([key, st, rate]);
      }
    });
    cands.sort(function (a, b) { return b[2] - a[2]; });
    return cands.slice(0, p.max_report).map(function (c) {
      return mk(doc, rule, c[1].first, c[1].first + c[0].length, {
        count: c[1].total, rate: round(c[2], 1), limit: p.max_per_1000,
        detail: "'" + c[0] + "' appears " + c[1].total + " times (" + fx(c[2], 1) + " per 1000 words)"
      });
    });
  };

  METRICS.echo_words = function (doc, rule, p, stop) {
    var pos = new Map();
    doc.tokens.forEach(function (t, ti) {
      var tok = t[0], c0 = tok.charAt(0);
      if (tok.length < p.min_len || !(c0 >= "a" && c0 <= "z") || stop[tok.toLowerCase()] === true) return;
      var k = tok.toLowerCase();
      if (!pos.has(k)) pos.set(k, []);
      pos.get(k).push(ti);
    });
    var hits = [], r = p.repeats;
    pos.forEach(function (lst, w) {
      var i = 0;
      while (i + r - 1 < lst.length) {
        if (lst[i + r - 1] - lst[i] < p.window) { hits.push([doc.tokens[lst[i]][1], w, r]); i += r; }
        else i++;
      }
    });
    hits.sort(function (a, b) { return a[0] - b[0]; });
    return hits.slice(0, p.max_report).map(function (h) {
      return mk(doc, rule, h[0], h[0] + h[1].length, { count: h[2], detail: "'" + h[1] + "' used " + h[2] + " times within " + p.window + " words" });
    });
  };

  function ngramRepeat(docs, rule, stop) {
    var p = rule.params, n = p.n;
    var counts = new Map(), chap = new Map(), first = new Map(), locs = new Map();
    docs.forEach(function (doc, fi) {
      doc.sentences.forEach(function (s) {
        var toks = [];
        for (var k = s.first; k < s.last; k++) toks.push(doc.tokens[k][0].toLowerCase());
        for (var a = 0; a + n <= toks.length; a++) {
          var g = toks.slice(a, a + n), content = 0;
          for (var b = 0; b < n; b++) if (stop[g[b]] !== true) content++;
          if (content < p.min_content_words) continue;
          var key = g.join("\u0001"), off = doc.tokens[s.first + a][1];
          if (!counts.has(key)) { counts.set(key, 0); chap.set(key, new Set()); first.set(key, [fi, off]); locs.set(key, []); }
          counts.set(key, counts.get(key) + 1);
          chap.get(key).add(fi + ":" + doc.chapterIndex(off));
          if (locs.get(key).length < 5) locs.get(key).push([fi, off]);
        }
      });
    });
    var flagged = [];
    counts.forEach(function (c, key) { if (c >= p.min_total || chap.get(key).size >= p.min_chapters) flagged.push(key); });
    function cmpFirst(a, b) { var x = first.get(a), y = first.get(b); return x[0] - y[0] || x[1] - y[1]; }
    flagged.sort(cmpFirst);
    var phrases = [], tails = new Map();
    function tailKey(count, chapters, words) { return count + "|" + chapters + "|" + words.join("\u0001"); }
    flagged.forEach(function (key) {
      var g = key.split("\u0001");
      var tk = tailKey(counts.get(key), chap.get(key).size, g.slice(0, -1));
      var ph = tails.get(tk);
      if (ph !== undefined) {
        tails.delete(tk);
        ph.words.push(g[g.length - 1]);
        tails.set(tailKey(ph.count, ph.chapters, ph.words.slice(-(n - 1))), ph);
      } else {
        ph = { words: g.slice(), count: counts.get(key), chapters: chap.get(key).size, first: first.get(key), locs: locs.get(key) };
        phrases.push(ph);
        tails.set(tailKey(ph.count, ph.chapters, ph.words.slice(-(n - 1))), ph);
      }
    });
    phrases.sort(function (a, b) { return (b.count - a.count) || (a.first[0] - b.first[0]) || (a.first[1] - b.first[1]); });
    return phrases.slice(0, p.max_report).map(function (ph) {
      var doc = docs[ph.first[0]], text = ph.words.join(" ");
      return mk(doc, rule, ph.first[1], ph.first[1] + text.length, {
        count: ph.count, scope: "corpus", phrase: text,
        detail: "'" + text + "' appears " + ph.count + " times in " + ph.chapters + " chapter(s)",
        locations: ph.locs.map(function (l) { return { file: docs[l[0]].path, line: docs[l[0]].lineCol(l[1])[0] }; })
      });
    });
  }

  function wanted(rule, o) {
    if (o.disable[rule.id]) return false;
    if (o.categories.length && o.categories.indexOf(rule.category) < 0) return false;
    return SEV_RANK[rule.severity] >= SEV_RANK[o.minSeverity];
  }

  /**
   * files: [{path, text}], rules: parsed rules.json, opts: {disable:[], categories:[], minSeverity}
   */
  function analyzeFiles(files, rules, opts) {
    opts = opts || {};
    var o = { disable: {}, categories: opts.categories || [], minSeverity: opts.minSeverity || "info" };
    (opts.disable || []).forEach(function (d) { o.disable[d] = true; });
    var stop = {};
    (rules.stopwords || []).forEach(function (w) { stop[w] = true; });
    var active = rules.rules.filter(function (r) { return wanted(r, o); });
    var docs = files.map(function (f) { return new Doc(f.path, f.text); });
    var compiled = {};
    active.forEach(function (r) { if (r.type === "pattern" || r.type === "density") compiled[r.id] = compileRule(r); });
    var fileReports = docs.map(function (doc) {
      var findings = [];
      active.forEach(function (r) {
        if (r.type === "pattern") {
          matchesOf(doc, r, compiled[r.id]).forEach(function (m) { findings.push(mk(doc, r, m[0], m[1])); });
        } else if (r.type === "density") {
          if (doc.wordCount < (r.min_words || 0)) return;
          var ms = matchesOf(doc, r, compiled[r.id]);
          if (!ms.length) return;
          var rate = ms.length * 1000 / doc.wordCount;
          if (ms.length >= r.min_count && rate > r.max_per_1000) {
            var lines = [];
            ms.forEach(function (m) { var ln = doc.lineCol(m[0])[0]; if (lines.indexOf(ln) < 0) lines.push(ln); });
            findings.push(mk(doc, r, ms[0][0], ms[0][1], {
              count: ms.length, rate: round(rate, 1), limit: r.max_per_1000, lines: lines.slice(0, 8), scope: "document",
              detail: ms.length + " occurrences, " + fx(rate, 1) + " per 1000 words (limit " + r.max_per_1000 + ")"
            }));
          }
        } else if (r.type === "metric" && r.metric !== "ngram_repeat") {
          var fn = METRICS[r.metric];
          if (fn) fn(doc, r, r.params, stop).forEach(function (f) { findings.push(f); });
        }
      });
      findings.sort(function (a, b) {
        var x = a.offset === null ? -1 : a.offset, y = b.offset === null ? -1 : b.offset;
        if (x !== y) return x - y;
        return a.rule < b.rule ? -1 : a.rule > b.rule ? 1 : 0;
      });
      return {
        path: doc.path, words: doc.wordCount, sentences: doc.sentences.length, paragraphs: doc.paragraphs.length,
        chapters: doc.chapters.map(function (c) { return c.title; }), findings: findings
      };
    });
    var corpus = [];
    active.forEach(function (r) {
      if (r.type === "metric" && r.metric === "ngram_repeat" && docs.length) ngramRepeat(docs, r, stop).forEach(function (f) { corpus.push(f); });
    });
    return summarize(fileReports, corpus);
  }

  function summarize(fileReports, corpus) {
    var all = [], bySev = { error: 0, warn: 0, info: 0 }, byCat = {};
    fileReports.forEach(function (fr) { fr.findings.forEach(function (f) { all.push(f); }); });
    corpus.forEach(function (f) { all.push(f); });
    all.forEach(function (f) { bySev[f.severity]++; byCat[f.category] = (byCat[f.category] || 0) + 1; });
    var words = 0;
    fileReports.forEach(function (fr) { words += fr.words; });
    var scored = bySev.error + bySev.warn, sorted = {};
    Object.keys(byCat).sort().forEach(function (k) { sorted[k] = byCat[k]; });
    return {
      tool: "fiction-slop-lint", version: VERSION,
      disclaimer: "Style linter only. Findings are hints, not proof of how a text was written.",
      files: fileReports, corpus: corpus,
      summary: {
        files: fileReports.length, words: words, findings: all.length, by_severity: bySev, by_category: sorted,
        warn_and_error_per_1000_words: words ? round(scored * 1000 / words, 2) : 0
      }
    };
  }

  return { version: VERSION, analyzeFiles: analyzeFiles, normalize: normalize };
});
