#!/usr/bin/env python3
"""Build the separate files required for COMMAT-D-26-03061 resubmission."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / (
    f"resubmission/COMMAT-D-26-03061_{date.today().strftime('%Y%m%d')}"
)

DIRECT_FILES = {
    "manuscript/cover_letter_resubmission.txt": "01_Cover_Letter.txt",
    "manuscript/response_to_reviewers_copy_paste.txt": (
        "02_Response_to_Reviewers_Copy_Paste.txt"
    ),
    "manuscript/response_to_reviewers.pdf": "02_Response_to_Reviewers.pdf",
    "manuscript/li_mace_graphene_draft.pdf": "03_Revised_Manuscript.pdf",
    "manuscript/supporting_information.pdf": "05_Supporting_Information.pdf",
    "manuscript/highlights.txt": "07_Highlights.txt",
    "manuscript/graphical_abstract.png": "08_Graphical_Abstract.png",
    "manuscript/graphical_abstract_caption.txt": "09_Graphical_Abstract_Caption.txt",
}

MANUSCRIPT_SOURCE = {
    "manuscript/li_mace_graphene_draft.tex": "li_mace_graphene_draft.tex",
    "manuscript/results_scientific_reframe.tex": "results_scientific_reframe.tex",
    "manuscript/references.bib": "references.bib",
    "manuscript/figures/structure_models.png": "structure_models.png",
    "manuscript/figures/scientific_summary_strengthened.pdf": (
        "scientific_summary_strengthened.pdf"
    ),
}

SI_SOURCE = {
    "manuscript/supporting_information.tex": "supporting_information.tex",
    "manuscript/figures/dataset_family_counts.png": "dataset_family_counts.png",
    "manuscript/figures/site_energy_rankings_revised.pdf": (
        "site_energy_rankings_revised.pdf"
    ),
    "manuscript/figures/path_profiles_revised.pdf": "path_profiles_revised.pdf",
    "manuscript/figures/review_md_extended_msd_xy_traces.pdf": (
        "review_md_extended_msd_xy_traces.pdf"
    ),
}

SOURCE_REWRITES = {
    "li_mace_graphene_draft.tex": {
        r"\graphicspath{{figures/}}": r"\graphicspath{{./}}",
        "{figures/structure_models.png}": "{structure_models.png}",
    },
    "results_scientific_reframe.tex": {
        "{figures/scientific_summary_strengthened.pdf}": (
            "{scientific_summary_strengthened.pdf}"
        ),
    },
    "supporting_information.tex": {
        r"\graphicspath{{figures/}}": r"\graphicspath{{./}}",
    },
}

UPLOAD_GUIDE = """COMMAT-D-26-03061 RESUBMISSION UPLOAD ORDER

Portal metadata:

- Manuscript type: Research Article
- Manuscript subject area: Atomic Description
- Resubmission deadline: 13 October 2026
- Keywords: machine-learning interatomic potentials; MACE; artificial intelligence;
  battery materials; lithium adsorption; graphene defects
- Equal contribution: mark Yuhan Sun and Xiao Huang as equal contributors
- Funding: no specific grant funding
- Competing interests: no known competing financial or personal interests
- Data and code: supplied as article-linked Supplementary Data
- Generative-AI statement: included in the revised manuscript

Upload these as separate Editorial Manager items:

1. Responses in the peer-review platform
   Open 02_Response_to_Reviewers_Copy_Paste.txt and paste the matching response
   block into each "Reply to comment" field. The PDF is a local reference copy;
   upload 02_Response_to_Reviewers.pdf only if a separate response-file slot is
   offered later in the workflow.

2. Manuscript
   03_Revised_Manuscript.pdf

3. Manuscript Source Files
   04_Manuscript_Source.zip
   This ZIP is flat: every LaTeX source file and figure is at the archive root.

4. Supporting Information
   05_Supporting_Information.pdf

5. Supporting Information Source
   06_Supporting_Information_Source.zip
   This ZIP is also flat and contains no subfolders.

6. Highlights
   07_Highlights.txt

7. Graphical Abstract
   08_Graphical_Abstract.png

8. Graphical Abstract Caption (only if the system provides a caption slot)
   09_Graphical_Abstract_Caption.txt

9. Cover Letter
   01_Cover_Letter.txt

10. Data/Code or Supplementary Material for Review
    10_Reproducibility_Archive.zip

Do not upload 99_COMMAT-D-26-03061_All_Materials.zip. It is only a local
transfer copy containing the separate files above.
"""


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_source_zip(
    output: Path,
    members: dict[str, str],
) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, target in members.items():
            source = ROOT / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            if Path(target).name != target:
                raise ValueError(f"Source archive member is not flat: {target}")
            if target in SOURCE_REWRITES:
                content = source.read_text(encoding="utf-8")
                for old, new in SOURCE_REWRITES[target].items():
                    if old not in content:
                        raise ValueError(f"Missing source rewrite in {source}: {old}")
                    content = content.replace(old, new)
                archive.writestr(target, content)
            else:
                archive.write(source, target)


def build(output: Path, reproducibility_archive: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for source_name, target_name in DIRECT_FILES.items():
        source = ROOT / source_name
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, output / target_name)

    write_source_zip(
        output / "04_Manuscript_Source.zip",
        MANUSCRIPT_SOURCE,
    )
    write_source_zip(
        output / "06_Supporting_Information_Source.zip",
        SI_SOURCE,
    )

    if not reproducibility_archive.is_file():
        raise FileNotFoundError(reproducibility_archive)
    shutil.copy2(reproducibility_archive, output / "10_Reproducibility_Archive.zip")
    (output / "00_UPLOAD_ORDER.txt").write_text(UPLOAD_GUIDE, encoding="utf-8")

    checksum_files = sorted(
        path for path in output.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"
    )
    (output / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(path)}  {path.name}\n" for path in checksum_files),
        encoding="ascii",
    )

    master = output / "99_COMMAT-D-26-03061_All_Materials.zip"
    with zipfile.ZipFile(master, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.iterdir()):
            if path.is_file() and path != master:
                archive.write(path, path.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reproducibility-archive", type=Path, required=True)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    archive = (
        args.reproducibility_archive
        if args.reproducibility_archive.is_absolute()
        else ROOT / args.reproducibility_archive
    )
    build(output, archive)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
