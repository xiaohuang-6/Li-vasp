#!/usr/bin/env python3
"""Build the separate files required for COMMAT-D-26-03061 resubmission."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "resubmission/COMMAT-D-26-03061_20260824"

DIRECT_FILES = {
    "manuscript/cover_letter_resubmission.txt": "01_Cover_Letter.txt",
    "manuscript/response_to_reviewers.pdf": "02_Response_to_Reviewers.pdf",
    "manuscript/li_mace_graphene_draft.pdf": "03_Revised_Manuscript.pdf",
    "manuscript/supporting_information.pdf": "05_Supporting_Information.pdf",
    "manuscript/highlights.txt": "07_Highlights.txt",
    "manuscript/graphical_abstract.png": "08_Graphical_Abstract.png",
    "manuscript/graphical_abstract_caption.txt": "09_Graphical_Abstract_Caption.txt",
}

MANUSCRIPT_SOURCE = (
    "manuscript/li_mace_graphene_draft.tex",
    "manuscript/results_scientific_reframe.tex",
    "manuscript/references.bib",
    "manuscript/compile_manuscript.sh",
    "manuscript/figures/structure_models.png",
    "manuscript/figures/scientific_summary_reframe.pdf",
)

SI_SOURCE = (
    "manuscript/supporting_information.tex",
    "manuscript/compile_manuscript.sh",
    "manuscript/figures/dataset_family_counts.png",
    "manuscript/figures/site_energy_rankings_revised.pdf",
    "manuscript/figures/path_profiles_revised.pdf",
    "manuscript/figures/review_md_extended_msd_xy_traces.pdf",
)

UPLOAD_GUIDE = """COMMAT-D-26-03061 RESUBMISSION UPLOAD ORDER

Upload these as separate Editorial Manager items:

1. Response to Reviewers
   02_Response_to_Reviewers.pdf

2. Manuscript
   03_Revised_Manuscript.pdf

3. Manuscript Source Files
   04_Manuscript_Source.zip

4. Supporting Information
   05_Supporting_Information.pdf

5. Supporting Information Source
   06_Supporting_Information_Source.zip

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


def write_source_zip(output: Path, members: tuple[str, ...], prefix: str) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in members:
            source = ROOT / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            path = Path(relative)
            if path.parts[:2] == ("manuscript", "figures"):
                target = Path(prefix) / "figures" / path.name
            else:
                target = Path(prefix) / path.name
            archive.write(source, target.as_posix())


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
        "Manuscript_Source",
    )
    write_source_zip(
        output / "06_Supporting_Information_Source.zip",
        SI_SOURCE,
        "Supporting_Information_Source",
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
