"""Minimal .docx text extraction using only zipfile and xml.etree (no dependencies)."""

import re
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_XML_BYTES = 80 * 1024 * 1024
_HEADING = re.compile(r"^(?:heading\s*\d|title|subtitle)$", re.I)


class DocxError(ValueError):
    pass


def _para_text(p):
    parts = []
    for node in p.iter():
        tag = node.tag
        if tag == W + "t":
            parts.append(node.text or "")
        elif tag == W + "tab":
            parts.append("\t")
        elif tag in (W + "br", W + "cr"):
            parts.append("\n")
        elif tag == W + "noBreakHyphen":
            parts.append("-")
    return "".join(parts)


def _is_heading(p):
    ppr = p.find(W + "pPr")
    if ppr is None:
        return False
    style = ppr.find(W + "pStyle")
    if style is None:
        return False
    val = (style.get(W + "val") or "").replace("-", " ")
    return bool(_HEADING.match(val))


def docx_to_text(path):
    """Return the document text: one blank-line separated block per paragraph.

    Headings become Markdown style '# ' lines so chapter detection works.
    """
    try:
        with zipfile.ZipFile(path) as zf:
            try:
                info = zf.getinfo("word/document.xml")
            except KeyError as exc:
                raise DocxError("%s: not a Word document (word/document.xml missing)" % path) from exc
            if info.file_size > MAX_XML_BYTES:
                raise DocxError("%s: document.xml is unreasonably large" % path)
            data = zf.read(info)
    except zipfile.BadZipFile as exc:
        raise DocxError("%s: not a valid .docx file" % path) from exc
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise DocxError("%s: cannot parse document.xml: %s" % (path, exc)) from exc
    out = []
    for p in root.iter(W + "p"):
        text = _para_text(p).strip()
        if not text:
            continue
        if _is_heading(p):
            text = "# " + text.replace("\n", " ")
        out.append(text)
    return "\n\n".join(out) + "\n"
