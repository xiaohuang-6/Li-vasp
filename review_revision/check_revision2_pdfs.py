#!/usr/bin/env python3
"""Verify R2 PDF structure, colors, source ZIP, and response location labels.

Requires PyMuPDF and Pillow. Also renders every page for human layout review;
automated geometry checks do not replace inspecting those images.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile
import pymupdf as fitz
from PIL import Image, ImageDraw
from build_revision2 import ROOT, BASELINE, flatten

OUT = ROOT / "resubmission/COMMAT_R2_20260913"
WORK = ROOT / "tmp/revision2-build"
RENDER = ROOT / "tmp/pdfs/revision2"


def main() -> None:
    RENDER.mkdir(parents=True, exist_ok=True)
    evidence = {}
    for name in ("Revised_Manuscript_Clean", "Revised_Manuscript_Marked", "Response_to_Reviewers"):
        path = OUT / (name + ".pdf")
        document = fitz.open(path)
        texts = [page.get_text() for page in document]
        assert all(len(text.strip()) > 30 for text in texts), f"Blank page: {name}"
        fulltext = ''.join(texts)
        assert not any(char in fulltext for char in ("\ufffd", "\x00", "??")), f"Placeholder: {name}"
        if "?" in fulltext:
            # The R1 introduction has one genuine question, shown as deleted text.
            assert name.endswith("Marked") and fulltext.count("?") == 1
            assert "used for training?" in fulltext
            question_spans = [span for page in document for block in page.get_text("dict")["blocks"]
                              for line in block.get("lines", []) for span in line["spans"] if "?" in span["text"]]
            assert all(span["color"] == 0xff0000 for span in question_spans)
        colors = Counter()
        bad_geometry = []
        red_strikes = 0
        for number, page in enumerate(document, 1):
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        if not span["text"].strip():
                            continue
                        colors[span["color"]] += len(span["text"])
                        x0, y0, x1, y1 = span["bbox"]
                        if x0 < 15 or x1 > page.rect.width - 15 or y0 < 15 or y1 > page.rect.height - 15:
                            bad_geometry.append((number, span["text"], span["bbox"]))
            red_strikes += sum(d["color"] == (1.0, 0.0, 0.0) and any(
                item[0] == "l" and abs(item[1].y-item[2].y) < .2 for item in d["items"]
            ) for d in page.get_drawings())
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            pix.save(RENDER / f"{name}-{number:02}.png")
        assert not bad_geometry, bad_geometry
        fonts = {font[0] for page in document for font in page.get_fonts(full=True) if font[0]}
        for xref in fonts:
            if document.extract_font(xref)[3]:
                continue
            # Matplotlib Type 3 fonts embed glyph drawing streams, not a font file.
            obj = document.xref_object(xref)
            assert "/Subtype /Type3" in obj, (name, "unembedded font", xref)
            charprocs = re.search(r"/CharProcs (\d+) 0 R", obj)
            assert charprocs, (name, "missing Type3 glyphs", xref)
            streams = re.findall(r"\b(\d+) 0 R", document.xref_object(int(charprocs[1])))
            assert streams and all(document.xref_stream(int(s)) for s in streams)
        if name.endswith("Marked"):
            assert colors[0x0000ff] > 1000 and colors[0xff0000] > 1000 and colors[0] > 1000
            assert red_strikes > 100, "Missing red deletion lines"
            assert "Red strikeout: deleted text." in texts[0]
        if name.endswith("Clean"):
            assert colors[0xff0000] == 0, "Revision red remains in clean text"
            assert colors[0x0000ff] == 0, "Revision blue remains in clean text"
        for start in range(0, len(document), 4):
            sheet = Image.new("RGB", (1260, 1740), "#cccccc")
            draw = ImageDraw.Draw(sheet)
            for j in range(start, min(start+4, len(document))):
                im = Image.open(RENDER / f"{name}-{j+1:02}.png")
                im.thumbnail((620, 835))
                x = (j-start)%2*630; y = (j-start)//2*870
                sheet.paste(im, (x, y+25)); draw.text((x+10, y+4), f"{name} page {j+1}", fill="black")
            sheet.save(RENDER / f"{name}-contact-{start+1:02}.png")
        evidence[name] = {"pages": len(document), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "text_colors": dict(colors), "red_strike_segments": red_strikes,
                          "embedded_fonts": len(fonts), "placeholders": 0, "out_of_page_text": 0}

    aux = (WORK / "Revised_Manuscript_Clean.aux").read_text()
    labels = {m[1]: (int(m[2]), int(m[3])) for m in re.finditer(
        r"\\newlabel\{(r2:[^}]+)\}\{\{(\d+)\}\{(\d+)\}", aux)}
    clean = fitz.open(OUT / "Revised_Manuscript_Clean.pdf")
    for label, (line, page) in labels.items():
        # A line label must resolve to an actually printed left-margin number.
        words = clean[page-1].get_text("words")
        assert any(w[4] == str(line) and w[2] < 70 for w in words), (label, line, page)
    text = flatten("li_mace_graphene_draft.tex")
    baseline_si = subprocess.check_output(["git", "show", f"{BASELINE}:manuscript/supporting_information.tex"], cwd=ROOT, text=True)
    labels_si = re.findall(r"\\label\{((?:fig|tab):si_[^}]+)\}", baseline_si)
    assert len(labels_si) == 12
    assert all(text.count("\\label{" + label + "}") == 1 for label in labels_si)
    assert all(re.search(r"\\(?:ref|eqref)\{" + re.escape(label) + r"\}", text) for label in labels_si)
    # Compare numerical table cells, not prose words that legitimately changed.
    old_tables = re.findall(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", baseline_si, re.S)
    new_tables = re.findall(r"\\begin\{tabular\}(.*?)\\end\{tabular\}", text, re.S)
    def numeric_rows(table: str) -> tuple:
        return tuple(tuple(re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", row))
                     for row in table.split(r"\\")[1:] if re.search(r"&\s*[-+]?\d", row))
    assert Counter(numeric_rows(t) for t in old_tables) == Counter(numeric_rows(t) for t in new_tables)
    with zipfile.ZipFile(OUT / "Revised_Manuscript_Editable_Source.zip") as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == 8
        assert all('/' not in name for name in archive.namelist())
        source = archive.read("Revised_Manuscript_Clean.tex").decode()
        assert len(re.findall(r"\\begin\{figure\}", source)) == 6
        assert len(re.findall(r"\\begin\{table\}", source)) == 8
        assert "\\input{" not in source
    evidence["response_line_labels"] = labels
    evidence["migrated_figures_and_tables"] = labels_si
    evidence["table_numbers_unchanged"] = True
    evidence["flat_source_members"] = 8
    (RENDER / "automated_checks.json").write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
