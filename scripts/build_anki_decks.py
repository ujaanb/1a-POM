#!/usr/bin/env python3
"""Build POM Anki decks from study-hub lecture pages.

Each lecture becomes a deck of basic cards (one per revision prompt) and
cloze cards (every high-value fact in the answer). Topic packages contain
one subdeck per lecture. The script also writes the download bars into the
lecture, topic, and home pages.

Requires: genanki, beautifulsoup4
"""

from __future__ import annotations

import hashlib
import html
import re
import sys
from pathlib import Path

import genanki
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
TOPICS_DIR = SITE / "topics"
ANKI_DIR = SITE / "anki"

TOPICS = (
    ("cellular-biology", "Cellular Biology"),
    ("haematology", "Haematology"),
    ("immunity", "Immunity"),
    ("genetics", "Genetics"),
)

BASIC_MODEL = genanki.Model(
    1872345601,
    "POM Basic",
    fields=[
        {"name": "Front"},
        {"name": "Back"},
        {"name": "Lecture"},
        {"name": "Section"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": (
                '<div class="lecture">{{Lecture}} · {{Section}}</div>'
                '<div class="q">{{Front}}</div>'
            ),
            "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
        }
    ],
    css="""
.card { font-family: -apple-system, "Segoe UI", sans-serif; font-size: 18px;
  line-height: 1.45; color: #0c1f2e; background: #f7fbfb; text-align: left; }
.lecture { color: #5a7385; font-size: 12px; letter-spacing: .04em;
  text-transform: uppercase; margin-bottom: 8px; }
.q { font-weight: 650; margin-bottom: 4px; }
ul { margin: .4em 0 0 1.15em; padding: 0; }
li { margin: .35em 0; }
hr#answer { border: 0; border-top: 1px solid #d0dde6; margin: .8em 0; }
""",
)

CLOZE_MODEL = genanki.Model(
    1872345602,
    "POM Cloze",
    fields=[
        {"name": "Text"},
        {"name": "Extra"},
        {"name": "Lecture"},
    ],
    templates=[
        {
            "name": "Cloze",
            "qfmt": (
                '<div class="lecture">{{Lecture}}</div>'
                '<div class="q">{{Extra}}</div>'
                '<div class="fact">{{cloze:Text}}</div>'
            ),
            "afmt": (
                '<div class="lecture">{{Lecture}}</div>'
                '<div class="q">{{Extra}}</div>'
                '<div class="fact">{{cloze:Text}}</div>'
            ),
        }
    ],
    model_type=genanki.Model.CLOZE,
    css="""
.card { font-family: -apple-system, "Segoe UI", sans-serif; font-size: 18px;
  line-height: 1.45; color: #0c1f2e; background: #f7fbfb; text-align: left; }
.lecture { color: #5a7385; font-size: 12px; letter-spacing: .04em;
  text-transform: uppercase; margin-bottom: 8px; }
.q { font-weight: 650; margin: 0 0 10px; }
.fact { font-size: 18px; }
.cloze { font-weight: 700; color: #0e7c7b; }
hr#answer { border: 0; border-top: 1px solid #d0dde6; margin: .8em 0; }
.others { display: block; margin-top: .55em; color: #243b4a; font-size: 15px; }
""",
)

STOP = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is", "are",
    "was", "were", "be", "been", "being", "by", "with", "from", "that", "this",
    "these", "those", "it", "its", "as", "at", "into", "via", "which", "when",
    "where", "how", "what", "their", "they", "them", "than", "then", "not",
    "but", "if", "so", "can", "may", "such", "also", "only", "other", "more",
    "most", "between", "during", "after", "before", "within", "without",
    "using", "used", "use", "does", "do", "has", "have", "had", "will",
    "would", "about", "over", "under", "both", "each", "per", "etc", "ie",
    "eg", "i.e", "e.g", "there", "here", "because", "through", "following",
    "process", "allows", "allow", "results", "result", "including", "include",
    "includes", "another", "other", "others", "same", "different", "normal",
    "within", "across", "around", "after", "before", "while", "where", "whose",
    "should", "could", "might", "must", "need", "needs", "needed", "make",
    "makes", "made", "cause", "causes", "caused", "lead", "leads", "leading",
    "known", "called", "means", "mean", "type", "types", "form", "forms",
    "part", "parts", "main", "important", "specific", "generally", "usually",
    "often", "very", "high", "low", "large", "small", "new", "old", "due",
    "onto", "upon", "out", "off", "up", "down", "all", "any", "some", "many",
    "much", "few", "one", "two", "three", "four", "five", "first", "second",
    "third", "next", "then", "thus", "hence", "therefore", "however", "although",
    "though", "whether", "either", "neither", "nor", "yet", "still", "just",
    "like", "such", "able", "unable", "present", "absent", "found", "seen",
    "show", "shows", "shown", "give", "given", "gives", "take", "takes",
    "taken", "occur", "occurs", "occurred", "happens", "happen", "help",
    "helps", "helping", "role", "roles", "way", "ways", "example", "examples",
    "following", "above", "below", "between", "against", "along", "among",
    "towards", "toward", "inside", "outside", "related", "associated",
    "involved", "produce", "produces", "produced", "production", "increase",
    "increased", "decrease", "decreased", "change", "changes", "changed",
    "effect", "effects", "action", "actions", "function", "functions",
    "functional", "structure", "structures", "system", "systems", "body",
    "cells", "cell", "blood", "factor", "factors", "protein", "proteins",
    "molecule", "molecules", "disease", "diseases", "patient", "patients",
    "clinical", "relevant", "remaining", "regular", "enough", "ensure",
    "purpose", "prevent", "prevents", "remove", "removes", "product",
    "preserve", "showing", "diagram", "typically", "useful", "states",
    "continue", "continues", "catalyse", "catalyzed", "catalyzed",
    "catalysed", "catalyze", "catalyzes", "transferring", "allowing",
    "contains", "conducted",
    "adequate", "differently", "interact", "interaction", "interactions",
    "possible", "possibly", "likely", "unlikely", "further", "already",
    "really", "simply", "directly", "indirectly", "completely", "particularly",
    "especially", "approximately", "respectively", "additional", "additionally",
    "specifically", "previously", "subsequently", "together", "relatively",
    "significantly", "mainly", "mostly", "largely", "primarily", "initially",
    "finally", "eventually", "currently", "actually", "basically", "essentially",
    "potentially", "effectively", "normally", "generally", "usually", "often",
    "sometimes", "various", "several", "important", "including", "related",
    "associated", "according", "another", "without", "within", "overall",
    "particular", "certain", "common", "typical", "negative", "positive",
    "different", "similar", "called", "known", "means", "using", "used",
    "response", "responses", "mechanism", "mechanisms", "pathway", "pathways",
    "level", "levels", "number", "numbers", "amount", "amounts", "rate",
    "rates", "time", "times", "case", "cases", "group", "groups", "people",
    "human", "humans", "normal", "abnormal", "positive", "negative",
    "active", "inactive", "activation", "inhibition", "inhibits", "inhibit",
    "binding", "binds", "bind", "bound", "release", "released", "releases",
    "required", "requires", "require", "responsible", "leading", "result",
    "results", "resulting", "causing", "called", "named", "known", "describe",
    "described", "recall", "explain", "explained", "difference", "between",
    "compared", "comparison", "versus", "into", "from", "with", "without",
    "this", "that", "these", "those", "their", "there", "which", "when",
    "where", "what", "whose", "while", "during", "after", "before", "about",
    "above", "other", "another", "also", "only", "just", "even", "still",
    "well", "back", "away", "own", "same", "different", "various", "several",
    "multiple", "single", "double", "whole", "full", "total", "overall",
    "particular", "certain", "common", "typical", "usually", "often",
    "sometimes", "always", "never", "may", "might", "can", "cannot",
    "don't", "doesnt", "isn't", "aren't", "wasn't", "weren't",
}

ARROW_RE = re.compile(r"\s*(?:→|->|—>|–>|-->|⇒)\s*")
NUM_RE = re.compile(
    r"(?<![A-Za-z0-9\-])~?\d+(?:[.,]\d+)?(?:\^\d+)?(?:\s*[–\-]\s*\d+(?:[.,]\d+)?)?"
    r"(?:\s*[x×]\s*10\^?\d+)?"
    r"(?:\s*(?:%|percent|kDa|nm|µm|μm|um|mm|cm|mg|µg|μg|g|kg|mL|ml|L|"
    r"mmol|mol|hours?|hrs?|days?|weeks?|years?|minutes?|mins?|seconds?))?"
    r"(?![A-Za-z])",
    re.I,
)
HYPHEN_ID_RE = re.compile(r"\b[A-Za-z]{2,}[A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b")
SHORT_ID_RE = re.compile(r"\b(?:\d+[A-Za-z]|[A-Za-z]\d+)\b")
NEG_NUM_RE = re.compile(r"(?<![\w-])-\d+(?:[.,]\d+)?")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9+\-]*\b")
CHEM_RE = re.compile(
    r"\b(?:Fe2\+|Fe3\+|Fe²\+|Ca2\+|Na\+|K\+|Cl−|Cl-|H\+|O2|CO2|H2O|H2O2|NAD\+|NADH|NADPH|FADH2|FAD|ATP|ADP|AMP|GTP|GDP|CoA|Pi)\b"
)
FACTOR_RE = re.compile(
    r"\b(?:Factor|Protein|Type|Class|Group|HLA|CD|IL|TNF|IFN)\s*[-\s]?\s*[A-Z0-9IVX]+\b"
)
QUOTED_RE = re.compile(r"[“\"]([^”\"]{2,80})[”\"]")
PAREN_RE = re.compile(r"\(([^()]{2,70})\)")
MED_RE = re.compile(
    r"\b[A-Za-z][A-Za-z\-]{3,}(?:ase|osis|oses|itis|aemia|emia|philia|phil|"
    r"cytes?|globin|globins|kinase|ogen|ogens|poietin|lysis|penia|oma|omas|"
    r"pathy|pathies|trophy|uria|ergic)\b"
)
NAME_RE = re.compile(
    r"\b(?!(?:The|This|That|These|Those|It|Its|In|On|At|By|To|For|And|But|If|"
    r"Or|When|Where|How|What|Why|During|After|Before|Some|There|They|Also|"
    r"From|With|Of|As|Which|Recall|Describe|Explain|Give|A|An)\b)"
    r"[A-Z][A-Za-z0-9'’+\-]{2,}(?:\s+(?:[A-Z][A-Za-z0-9'’+\-]{1,}|von|de|di|van|da|[IVX]{1,6}|\d+[a-z]?)){0,5}"
)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+\-^'’]*")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z“\"])")
BAR_RE = re.compile(r'\n?<div class="anki-bar">.*?</div>\n?', re.S)


def normalize_science(text: str) -> str:
    """Fold subscripts, superscripts, and Greek letters so cloze spans stay intact."""
    text = text.translate(str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻₋−", "01234567890123456789+---"))
    for src, dst in (
        ("α", "alpha"),
        ("β", "beta"),
        ("γ", "gamma"),
        ("δ", "delta"),
        ("ε", "epsilon"),
        ("λ", "lambda"),
        ("κ", "kappa"),
        ("μ", "u"),
        ("µ", "u"),
        ("ω", "omega"),
        ("ºC", " C"),
        ("°C", " C"),
        ("º", ""),
        ("°", ""),
        ("–", "-"),
        ("—", "-"),
    ):
        text = text.replace(src, dst)
    return text


def clean(text: str) -> str:
    text = html.unescape(text).replace("\xa0", " ")
    text = text.replace("—>", "→").replace("–>", "→").replace("-->", "→")
    text = normalize_science(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def cloze_wrap(answer: str) -> str:
    inner = esc(answer).replace("}", ")").replace("{", "(")
    inner = inner.replace("::", "∶")
    return "{{c1::" + inner + "}}"


def mask(text: str, start: int, end: int) -> str:
    return esc(text[:start]) + cloze_wrap(text[start:end]) + esc(text[end:])


def deck_id(name: str) -> int:
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def guid_for(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def is_stop(token: str) -> bool:
    return token.lower().strip(".,;:") in STOP


def is_medical(token: str) -> bool:
    return bool(MED_RE.fullmatch(token))


def technical_token(token: str) -> bool:
    if is_stop(token):
        return False
    if any(ch.isdigit() for ch in token):
        return True
    if token.isupper() and len(token) >= 2:
        return True
    if is_medical(token):
        return True
    if token.lower() in {"sex", "gene", "genes", "ion", "ions", "exon", "exons", "codon"}:
        return True
    if token[:1].isupper() and len(token) >= 4:
        return True
    if len(token) >= 6:
        return True
    return False


def content_tokens(text: str) -> list[str]:
    return [tok for tok in WORD_RE.findall(text) if technical_token(tok)]


def add_span(cands: list[tuple[int, int, int]], start: int, end: int, score: int, text: str) -> None:
    if start < 0 or end > len(text) or end - start < 1:
        return
    chunk = text[start:end].strip()
    if len(chunk) < 1:
        return
    # trim surrounding punctuation from the span
    while chunk and chunk[0] in " ,;:":
        start += 1
        chunk = text[start:end]
    while chunk and chunk[-1] in " ,;:.":
        end -= 1
        chunk = text[start:end]
    if not chunk or chunk.lower().strip(".,;:") in STOP:
        return
    if len(chunk) == 1 and not chunk.isdigit():
        return
    cands.append((start, end, score))


def find_spans(text: str) -> list[tuple[int, int]]:
    cands: list[tuple[int, int, int]] = []
    for m in QUOTED_RE.finditer(text):
        add_span(cands, m.start(1), m.end(1), 92, text)
    for m in NEG_NUM_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 97, text)
    for m in NUM_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 96, text)
    for m in CHEM_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 95, text)
    for m in FACTOR_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 94, text)
    for m in ACRONYM_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 90, text)
    for m in SHORT_ID_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 91, text)
    for m in HYPHEN_ID_RE.finditer(text):
        token = m.group()
        if any(ch.isdigit() for ch in token) or token.isupper():
            add_span(cands, m.start(), m.end(), 93, text)
    for m in PAREN_RE.finditer(text):
        inner = m.group(1).strip()
        trimmed = re.sub(r"^(?:i\.e\.?|e\.g\.?|eg|ie)\s+", "", inner, flags=re.I).strip()
        if trimmed:
            rel = inner.lower().find(trimmed.lower())
            if rel < 0:
                rel = 0
            add_span(cands, m.start(1) + rel, m.start(1) + rel + len(trimmed), 84, text)
        before = text[: m.start()].rstrip()
        wm = re.search(r"([A-Za-z][A-Za-z0-9'’+\-]{2,})\s*$", before)
        if wm and technical_token(wm.group(1)):
            add_span(cands, wm.start(1), wm.end(1), 82, text)
    for m in MED_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 70, text)
    for m in NAME_RE.finditer(text):
        add_span(cands, m.start(), m.end(), 68, text)
    for m in WORD_RE.finditer(text):
        token = m.group()
        if token[:1].isupper() or token.isupper() or any(ch.isdigit() for ch in token):
            continue
        if technical_token(token):
            add_span(cands, m.start(), m.end(), 58, text)

    cands.sort(key=lambda item: (-item[2], -(item[1] - item[0]), item[0]))
    chosen: list[tuple[int, int]] = []
    seen_chunks: set[str] = set()
    for start, end, _score in cands:
        if any(not (end <= s or start >= e) for s, e in chosen):
            continue
        if chosen and (end - start) >= int(len(text) * 0.85):
            continue
        chunk_key = text[start:end].strip().lower()
        if chunk_key in seen_chunks:
            continue
        seen_chunks.add(chunk_key)
        chosen.append((start, end))
    chosen.sort()
    return chosen


def split_definition(fact: str) -> tuple[str, str] | None:
    for sep in (" — ", " – ", " - ", ": "):
        if sep not in fact:
            continue
        left, right = fact.split(sep, 1)
        left, right = left.strip(), right.strip()
        if len(left) < 2 or len(right) < 2 or len(left) > 90:
            continue
        if left.endswith("."):
            continue
        low = left.lower()
        if low.startswith(("i.e", "e.g", "eg", "ie")):
            continue
        if sep == ": " and (len(left) > 42 or len(left.split()) > 6):
            continue
        if len(left.split()) > 12:
            continue
        return left, right
    return None


def is_short_item(fact: str) -> bool:
    if len(fact) > 100 or len(fact.split()) > 14:
        return False
    if " - " in fact or " — " in fact or " – " in fact:
        return False
    return True


def variants_for_piece(piece: str, allow_whole: bool) -> list[str]:
    piece = piece.strip()
    if not piece:
        return []
    variants: list[str] = []
    seen: set[str] = set()

    def add(variant: str) -> None:
        key = re.sub(r"\s+", " ", variant).strip()
        if key and key not in seen and "{{c1::" in key:
            seen.add(key)
            variants.append(key)

    parts = [p.strip() for p in ARROW_RE.split(piece) if p.strip()]
    if 2 <= len(parts) <= 8 and all(1 <= len(p) <= 80 for p in parts):
        for i in range(len(parts)):
            segs = [cloze_wrap(p) if i == j else esc(p) for j, p in enumerate(parts)]
            add(" → ".join(segs))
        return variants

    definition = split_definition(piece)
    if definition:
        left, right = definition
        add(f"{cloze_wrap(left)} — {esc(right)}")
        right_words = len(right.split())
        if right_words <= 10:
            add(f"{esc(left)} — {cloze_wrap(right)}")
        else:
            spans = find_spans(right)
            if spans:
                for start, end in spans:
                    if right[start:end].strip() == right.strip():
                        continue
                    add(f"{esc(left)} — {mask(right, start, end)}")
            else:
                add(f"{esc(left)} — {cloze_wrap(right)}")
        return variants

    spans = find_spans(piece)
    partial = False
    for start, end in spans:
        chunk = piece[start:end].strip()
        if chunk == piece.strip():
            continue
        partial = True
        add(mask(piece, start, end))
    words = len(piece.split())
    if allow_whole and (not partial or words <= 3):
        add(cloze_wrap(piece.strip()))
    elif allow_whole and not variants:
        add(cloze_wrap(piece.strip()))
    return variants


def sentence_pieces(fact: str) -> list[str]:
    if split_definition(fact) or (ARROW_RE.search(fact) and len(ARROW_RE.split(fact)) >= 2):
        return [fact]
    parts = [p.strip() for p in SENT_RE.split(fact) if p.strip()]
    return parts or [fact]


def cloze_variants_for_fact(fact: str, allow_whole: bool) -> list[str]:
    variants: list[str] = []
    seen: set[str] = set()
    for piece in sentence_pieces(fact):
        for variant in variants_for_piece(piece, allow_whole=allow_whole):
            if variant not in seen:
                seen.add(variant)
                variants.append(variant)
    # cover any high-value token still missing from cloze answers
    covered = " ".join(cloze_inners(v) for v in variants).lower()
    missing = []
    seen_missing: set[str] = set()
    for tok in content_tokens(fact):
        key = tok.lower()
        if token_covered(covered, key) or key in seen_missing:
            continue
        seen_missing.add(key)
        missing.append(tok)
    missing.sort(key=len, reverse=True)
    added = 0
    for tok in missing:
        match = re.search(rf"(?<!\w){re.escape(tok)}(?!\w)", fact)
        if not match:
            continue
        variant = mask(fact, match.start(), match.end())
        if variant not in seen:
            seen.add(variant)
            variants.append(variant)
            covered = (covered + " " + tok).lower()
            added += 1
    if not variants and allow_whole and fact.strip():
        variants.append(cloze_wrap(fact.strip()))
    return variants


def cloze_inners(variant: str) -> str:
    return " ".join(html.unescape(part) for part in re.findall(r"\{\{c1::(.*?)\}\}", variant))


def token_covered(blob: str, token: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(token.lower())}(?!\w)", blob) is not None


def list_gap_variants(question: str, shorts: list[str]) -> list[str]:
    """Hide one short list item and leave the others visible so the blank is determined."""
    if len(shorts) < 2:
        return []
    variants = []
    for index, item in enumerate(shorts):
        others = [esc(other) for i, other in enumerate(shorts) if i != index]
        shown = "; ".join(others)
        variants.append(
            f"{cloze_wrap(item)}<br><span class=\"others\">Other items: {shown}</span>"
        )
    return variants


def answer_html(parts: list[str]) -> str:
    if len(parts) == 1:
        return f"<div>{esc(parts[0])}</div>"
    items = "".join(f"<li>{esc(part)}</li>" for part in parts)
    return f"<ul>{items}</ul>"


def parse_lecture(path: Path) -> dict:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    title = clean(soup.find("h1").get_text(" ", strip=True))
    blocks = []
    notes = soup.select_one("div.notes") or soup
    for section in notes.select("section.panel"):
        heading = section.find("h2")
        section_name = clean(heading.get_text(" ", strip=True)) if heading else "Overview"
        for qa in section.select("div.qa"):
            h3 = qa.find("h3")
            if not h3:
                continue
            question = clean(h3.get_text(" ", strip=True))
            parts: list[str] = []
            for child in qa.children:
                name = getattr(child, "name", None)
                if name in (None, "h3"):
                    continue
                classes = child.get("class") or []
                if "source-note" in classes:
                    continue
                if name in ("ul", "ol"):
                    for li in child.find_all("li", recursive=False):
                        text = clean(li.get_text(" ", strip=True))
                        if text:
                            parts.append(text)
                elif name == "p":
                    text = clean(child.get_text(" ", strip=True))
                    if text:
                        parts.append(text)
                elif name == "table":
                    for row in child.find_all("tr"):
                        cells = [clean(td.get_text(" ", strip=True)) for td in row.find_all(["th", "td"])]
                        cells = [cell for cell in cells if cell]
                        if cells:
                            parts.append(" — ".join(cells))
            if question and parts:
                blocks.append({"section": section_name, "question": question, "parts": parts})
        for fig in section.find_all("figure"):
            label = clean(fig.get("aria-label") or "")
            if not label:
                cap = fig.find("figcaption")
                label = clean(cap.get_text(" ", strip=True)) if cap else "Lecture diagram"
            labels = diagram_labels(fig)
            if labels:
                q = f"What labels are shown on the diagram “{label}”?"
                blocks.append({"section": section_name, "question": q, "parts": labels, "diagram": True})
    return {"title": title, "slug": path.stem, "blocks": blocks}


def diagram_labels(fig) -> list[str]:
    nodes = []
    for node in fig.find_all("text"):
        text = clean(node.get_text(" ", strip=True))
        if not text:
            continue
        try:
            x = float(node.get("x") or 0)
            y = float(node.get("y") or 0)
        except ValueError:
            x, y = 0.0, 0.0
        nodes.append([y, x, text])
    nodes.sort()
    merged: list[list] = []
    for y, x, text in nodes:
        if (
            merged
            and abs(x - merged[-1][1]) < 36
            and 0 < (y - merged[-1][0]) < 24
            and len(merged[-1][2]) < 40
        ):
            merged[-1][2] = clean(merged[-1][2] + " " + text)
            merged[-1][0] = y
        else:
            merged.append([y, x, text])
    labels = []
    for _y, _x, text in merged:
        if re.fullmatch(r"[IVX]{1,4}", text):
            continue
        if len(text) < 2:
            continue
        if text not in labels:
            labels.append(text)
    return labels


def notes_for_lecture(lecture: dict, topic_slug: str) -> tuple[list[genanki.Note], list[genanki.Note]]:
    basic_notes: list[genanki.Note] = []
    cloze_notes: list[genanki.Note] = []
    title = lecture["title"]
    seen_cloze: set[str] = set()
    for block_index, block in enumerate(lecture["blocks"]):
        question = block["question"]
        parts = block["parts"]
        section = block["section"]
        basic = genanki.Note(
            model=BASIC_MODEL,
            fields=[question, answer_html(parts), title, section],
            tags=["pom", topic_slug, "basic", slug_tag(lecture["slug"])],
            guid=guid_for(f"basic|{title}|{block_index}|{question}"),
        )
        basic_notes.append(basic)

        shorts = [part for part in parts if is_short_item(part)]
        use_list = len(shorts) >= 2
        if use_list:
            for variant in list_gap_variants(question, shorts):
                add_cloze(
                    cloze_notes,
                    seen_cloze,
                    variant,
                    question,
                    title,
                    topic_slug,
                    lecture["slug"],
                    f"list|{block_index}|{variant}",
                )
        for part_index, part in enumerate(parts):
            allow_whole = not (use_list and is_short_item(part))
            for variant in cloze_variants_for_fact(part, allow_whole=allow_whole):
                add_cloze(
                    cloze_notes,
                    seen_cloze,
                    variant,
                    question,
                    title,
                    topic_slug,
                    lecture["slug"],
                    f"fact|{block_index}|{part_index}|{variant}",
                )
    return basic_notes, cloze_notes


def slug_tag(slug: str) -> str:
    return "lecture-" + re.sub(r"[^a-z0-9\-]+", "-", slug.lower())


def add_cloze(bucket, seen, variant, question, title, topic_slug, lecture_slug, key):
    dedup = variant + "||" + question
    if dedup in seen:
        return
    seen.add(dedup)
    bucket.append(
        genanki.Note(
            model=CLOZE_MODEL,
            fields=[variant, esc(question), title],
            tags=["pom", topic_slug, "cloze", slug_tag(lecture_slug)],
            guid=guid_for(f"cloze|{title}|{key}"),
        )
    )


def lecture_order(topic_slug: str) -> list[str]:
    index = TOPICS_DIR / topic_slug / "index.html"
    soup = BeautifulSoup(index.read_text(encoding="utf-8"), "html.parser")
    slugs = []
    for link in soup.select("a.lecture-card"):
        href = link.get("href") or ""
        if href.endswith(".html"):
            slugs.append(Path(href).stem)
    return slugs


def build_deck(name: str, notes: list[genanki.Note]) -> genanki.Deck:
    deck = genanki.Deck(deck_id(name), name)
    for note in notes:
        deck.add_note(note)
    return deck


def upsert_bar(path: Path, bar: str) -> None:
    text = path.read_text(encoding="utf-8")
    if 'class="anki-bar"' in text:
        text = BAR_RE.sub(bar, text, count=1)
    else:
        match = re.search(r'<p class="page-lead">.*?</p>', text)
        if not match:
            raise SystemExit(f"No page-lead in {path}")
        text = text[: match.end()] + bar + text[match.end() :]
    path.write_text(text, encoding="utf-8")


def update_home(counts: dict[str, int]) -> None:
    path = SITE / "index.html"
    text = path.read_text(encoding="utf-8")
    links = []
    for slug, name in TOPICS:
        total = counts[slug]
        links.append(
            f'        <a class="hero-cta hero-cta-secondary" href="anki/{slug}.apkg" download>'
            f"Anki: {name} ({total})</a>"
        )
    block = "\n".join(links)
    text2, n = re.subn(
        r'\s*<a class="hero-cta hero-cta-secondary" href="anki/[^"]+\.apkg"[^>]*>.*?</a>',
        "",
        text,
    )
    if n == 0 and "anki/" not in text2:
        pass
    # insert the four links after the practice-questions button
    needle = '<a class="hero-cta hero-cta-secondary" href="practice.html">Practice questions →</a>'
    if needle not in text2:
        raise SystemExit("Home hero markup changed; could not insert Anki links")
    text2 = text2.replace(needle, needle + "\n" + block, 1)
    path.write_text(text2, encoding="utf-8")


def load_topic(topic_slug: str) -> list[dict]:
    lectures = []
    for slug in lecture_order(topic_slug):
        path = TOPICS_DIR / topic_slug / f"{slug}.html"
        if not path.exists():
            raise SystemExit(f"Missing lecture page {path}")
        lectures.append(parse_lecture(path))
    return lectures


def coverage_problems(lecture: dict) -> list[str]:
    problems = []
    for block in lecture["blocks"]:
        shorts = [part for part in block["parts"] if is_short_item(part)]
        use_list = len(shorts) >= 2
        produced = []
        if use_list:
            produced.extend(list_gap_variants(block["question"], shorts))
        for part in block["parts"]:
            produced.extend(
                cloze_variants_for_fact(part, allow_whole=not (use_list and is_short_item(part)))
            )
        covered = " ".join(cloze_inners(v) for v in produced).lower()
        for part in block["parts"]:
            missing = [tok for tok in content_tokens(part) if not token_covered(covered, tok)]
            if missing:
                problems.append(f"{block['question'][:60]} :: {missing[:6]}")
    return problems


def render_sample(slug: str, limit: int) -> None:
    for topic_slug, _name in TOPICS:
        path = TOPICS_DIR / topic_slug / f"{slug}.html"
        if path.exists():
            lecture = parse_lecture(path)
            basic, cloze = notes_for_lecture(lecture, topic_slug)
            print(f"{lecture['title']}: {len(basic)} basic, {len(cloze)} cloze")
            shown = 0
            for note in cloze:
                if shown >= limit:
                    break
                print("---")
                print("Q:", note.fields[1])
                print("T:", note.fields[0][:400])
                shown += 1
            problems = coverage_problems(lecture)
            print(f"coverage gaps: {len(problems)}")
            for line in problems[:12]:
                print(" GAP", line)
            return
    raise SystemExit(f"No lecture named {slug}")


def main() -> None:
    sample = None
    limit = 30
    args = sys.argv[1:]
    if "--sample" in args:
        sample = args[args.index("--sample") + 1]
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    if sample:
        render_sample(sample, limit)
        return

    ANKI_DIR.mkdir(parents=True, exist_ok=True)
    topic_counts: dict[str, int] = {}
    for topic_slug, topic_name in TOPICS:
        lectures = load_topic(topic_slug)
        lecture_dir = ANKI_DIR / "lectures" / topic_slug
        lecture_dir.mkdir(parents=True, exist_ok=True)
        topic_decks = []
        topic_total = 0
        gap_total = 0
        for lecture in lectures:
            basic, cloze = notes_for_lecture(lecture, topic_slug)
            gaps = coverage_problems(lecture)
            gap_total += len(gaps)
            deck_name = f"POM::{topic_name}::{lecture['title']}"
            deck = build_deck(deck_name, basic + cloze)
            lecture_path = lecture_dir / f"{lecture['slug']}.apkg"
            genanki.Package(deck).write_to_file(lecture_path)
            topic_decks.append(deck)
            total = len(basic) + len(cloze)
            topic_total += total
            page = TOPICS_DIR / topic_slug / f"{lecture['slug']}.html"
            upsert_bar(
                page,
                (
                    '\n<div class="anki-bar">'
                    f'<a class="anki-all" href="../../anki/lectures/{topic_slug}/{lecture["slug"]}.apkg" download>'
                    "Download this lecture (Anki)</a>"
                    f'<a href="../../anki/{topic_slug}.apkg" download>Download all {esc(topic_name)}</a>'
                    f"<span>{total} cards · {len(basic)} basic · {len(cloze)} cloze</span>"
                    "</div>\n"
                ),
            )
            print(f"{lecture['title']}: {len(basic)} basic, {len(cloze)} cloze, gaps {len(gaps)}")
        topic_package = ANKI_DIR / f"{topic_slug}.apkg"
        genanki.Package(topic_decks).write_to_file(topic_package)
        upsert_bar(
            TOPICS_DIR / topic_slug / "index.html",
            (
                '\n<div class="anki-bar">'
                f'<a class="anki-all" href="../../anki/{topic_slug}.apkg" download>'
                f"Download all {esc(topic_name)} (Anki)</a>"
                f"<span>{topic_total} cards across {len(lectures)} lectures · basic and cloze</span>"
                "</div>\n"
            ),
        )
        topic_counts[topic_slug] = topic_total
        print(f"== {topic_name}: {topic_total} cards, coverage gaps {gap_total}")
    update_home(topic_counts)
    print("wrote decks and download links")


if __name__ == "__main__":
    main()
