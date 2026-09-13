#!/usr/bin/env python3
"""Build the complete second-resubmission package, including tracked changes."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from xml.sax.saxutils import escape
from build_revision2 import ROOT
from build_reproducibility_archive import verify_archive

GUIDE = """COMMAT-D-26-03061R1: SECOND RESUBMISSION
Deadline in the editor's 12 September decision: 12 October 2026.

Extract this transfer package locally. Do not upload the outer ZIP to the portal.

Required item                         File
Graphical abstract                    Graphical_Abstract.png
Declaration of competing interests    Declaration_of_Competing_Interests.docx
Revised manuscript (unmarked source)  Revised_Manuscript_Editable_Source.zip
Revised manuscript (marked up)        Revised_Manuscript_Marked.pdf

The editable source ZIP is flat and contains the full MAIN manuscript and all
six figures. Revised_Manuscript_Clean.pdf is the identical text for your review.
The marked PDF compares R2 with R1 and has a color legend on its first page.
All response page/line references refer to Revised_Manuscript_Clean.pdf.

Additional items:
- Paste the matching blocks from Response_to_Reviewers_Copy_Paste.txt into
  the peer-review platform. Response_to_Reviewers.pdf is a reference copy or
  a separate response upload if the portal offers that slot.
- Upload Highlights.txt as Highlights.
- Upload Cover_Letter.txt as the cover letter.
- Upload Reproducibility_Archive.zip as Supplementary Data, not LaTeX source.
  Its directory structure is for data/code, not the manuscript PDF builder.
- Graphical_Abstract_Caption.txt is supplied if a separate caption is requested.

There is no separate R2 SI PDF: all previous SI figures and tables are in the
main article. Remove the superseded R1 SI and obsolete R1 manuscript uploads.
Upload_Four_Required_Items.zip contains exactly the four primary files above;
extract it first and assign each file to its own item type.
"""


def declaration_docx(path: Path) -> None:
    paragraphs = ["Declaration of competing interests",
        "The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper."]
    xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", xml + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr("_rels/.rels", xml + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        body = ''.join('<w:p><w:r><w:t>' + escape(p) + '</w:t></w:r></w:p>' for p in paragraphs)
        archive.writestr("word/document.xml", xml + '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr></w:body></w:document>')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "resubmission/COMMAT_R2_20260913")
    parser.add_argument("--reproducibility-archive", type=Path, required=True)
    parser.add_argument("--tectonic", default="tectonic")
    parser.add_argument("--latexdiff", default="latexdiff")
    args = parser.parse_args()
    out = args.output.resolve()
    errors = verify_archive(args.reproducibility_archive)
    if errors:
        raise RuntimeError("\n".join(errors))
    for script, options in [
        ("build_revision2.py", ["--latexdiff", args.latexdiff]),
        ("write_revision2_response.py", []),
    ]:
        subprocess.run([sys.executable, str(ROOT / "review_revision" / script),
            "--output", str(out), "--tectonic", args.tectonic, *options], check=True)
    copies = {
        "graphical_abstract.png": "Graphical_Abstract.png",
        "graphical_abstract_caption.txt": "Graphical_Abstract_Caption.txt",
        "highlights.txt": "Highlights.txt",
        "cover_letter_resubmission.txt": "Cover_Letter.txt",
    }
    for source, target in copies.items():
        shutil.copy2(ROOT / "manuscript" / source, out / target)
    shutil.copy2(args.reproducibility_archive, out / "Reproducibility_Archive.zip")
    declaration_docx(out / "Declaration_of_Competing_Interests.docx")
    (out / "00_UPLOAD_GUIDE.txt").write_text(GUIDE)
    four = ["Graphical_Abstract.png", "Declaration_of_Competing_Interests.docx",
            "Revised_Manuscript_Editable_Source.zip", "Revised_Manuscript_Marked.pdf"]
    with zipfile.ZipFile(out / "Upload_Four_Required_Items.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in four:
            archive.write(out / name, name)
    master = out / "COMMAT_R2_All_Materials.zip"
    files = sorted(p for p in out.iterdir() if p.is_file() and p.name not in {master.name, "SHA256SUMS.txt"})
    (out / "SHA256SUMS.txt").write_text(''.join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files))
    with zipfile.ZipFile(master, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files + [out / "SHA256SUMS.txt"]:
            archive.write(path, path.name)
    print(master)


if __name__ == "__main__":
    main()
