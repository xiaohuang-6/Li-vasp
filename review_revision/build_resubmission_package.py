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
    "manuscript/figures/scientific_summary_strengthened.pdf",
    "manuscript/figures/scientific_summary_strengthened.png",
    "make_structure_figure.py",
    "review_revision/plot_science_strengthening_summary.py",
    "structures/vasp/POSCAR_A_Perfect.vasp",
    "structures/vasp/POSCAR_B1_Monovacancy.vasp",
    "structures/vasp/POSCAR_B2_Divacancy.vasp",
    "structures/vasp/POSCAR_C_StoneWales.vasp",
    "structures/vasp/POSCAR_D_SiGraphene.vasp",
    "submission_data/structures/relaxed/A_Perfect.vasp",
    "submission_data/structures/relaxed/B1_Monovacancy.vasp",
    "submission_data/structures/relaxed/B2_Divacancy.vasp",
    "submission_data/structures/relaxed/C_StoneWales.vasp",
    "submission_data/structures/relaxed/D_SiGraphene.vasp",
    "submission_data/results/d3_site_adsorption_energies.csv",
    "submission_data/results/balanced_perturbation_force_errors.csv",
    "submission_data/results/balanced_perturbation_force_summary.csv",
    "submission_data/results/foundation_snapshot_force_errors.csv",
    "submission_data/results/foundation_snapshot_force_summary.csv",
    "submission_data/results/grouped_e0_snapshot_force_errors.csv",
    "submission_data/results/grouped_e0_snapshot_force_summary.csv",
)

SI_SOURCE = (
    "manuscript/supporting_information.tex",
    "manuscript/compile_manuscript.sh",
    "manuscript/figures/dataset_family_counts.png",
    "manuscript/figures/site_energy_rankings_revised.pdf",
    "manuscript/figures/site_energy_rankings_revised.png",
    "manuscript/figures/path_profiles_revised.pdf",
    "manuscript/figures/path_profiles_revised.png",
    "manuscript/figures/review_md_extended_msd_xy_traces.pdf",
    "manuscript/figures/review_md_extended_msd_xy_traces.png",
    "review_revision/plot_dataset_family_counts.py",
    "review_revision/plot_si_msd_traces.py",
    "review_revision/plot_si_site_path.py",
    "submission_data/datasets/grouped_split/train.extxyz",
    "submission_data/datasets/grouped_split/valid.extxyz",
    "submission_data/datasets/grouped_split/test.extxyz",
    "submission_data/results/fixed_site_energies.csv",
    "submission_data/results/fixed_path_profiles.csv",
    "submission_data/results/review_md_msd_traces_sampled.csv",
)

MANUSCRIPT_SOURCE_README = """EDITABLE MANUSCRIPT SOURCE

Compile the article from this directory:
  bash compile_manuscript.sh

Regenerate the two manuscript figures:
  python make_structure_figure.py --output-dir figures
  python review_revision/plot_science_strengthening_summary.py \\
    --output figures/scientific_summary_strengthened
"""

SI_SOURCE_README = """EDITABLE SUPPORTING INFORMATION SOURCE

Compile the Supporting Information from this directory:
  bash compile_manuscript.sh supporting_information.tex

Regenerate the Supporting Information figures:
  python review_revision/plot_dataset_family_counts.py \\
    --output figures/dataset_family_counts.png
  python review_revision/plot_si_site_path.py --output-dir figures
  python review_revision/plot_si_msd_traces.py \\
    --output figures/review_md_extended_msd_xy_traces.png
"""

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
- Generative-AI statement: no separate manuscript declaration is included

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


def write_source_zip(
    output: Path,
    members: tuple[str, ...],
    prefix: str,
    readme: str,
) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in members:
            source = ROOT / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            path = Path(relative)
            if path.parts[0] == "manuscript":
                target = Path(prefix).joinpath(*path.parts[1:])
            else:
                target = Path(prefix) / path
            archive.write(source, target.as_posix())
        archive.writestr(f"{prefix}/00_README.txt", readme)


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
        MANUSCRIPT_SOURCE_README,
    )
    write_source_zip(
        output / "06_Supporting_Information_Source.zip",
        SI_SOURCE,
        "Supporting_Information_Source",
        SI_SOURCE_README,
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
