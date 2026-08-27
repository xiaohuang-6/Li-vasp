#!/usr/bin/env python3
"""Prepare two-stage, dipole-corrected D3 jobs for the frozen 15-site design."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from ase.io import read


STAGE1_TEMPLATE = """SYSTEM = D3 precondition {system}
ENCUT = 520
EDIFF = 1E-6
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = .FALSE.
ALGO = Normal
NCORE = 4
IBRION = -1
NSW = 0
ISIF = 2
ISPIN = 2
ISYM = 0
LASPH = .TRUE.
ADDGRID = .TRUE.
IVDW = 12
LDIPOL = .FALSE.
LWAVE = .TRUE.
LCHARG = .TRUE.
NELM = 180
MAGMOM = {magmom}
"""

STAGE2_TEMPLATE = """SYSTEM = D3 dipole converged {system}
ENCUT = 520
EDIFF = 1E-6
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = .FALSE.
ALGO = All
TIME = 0.4
NCORE = 4
ISTART = 1
ICHARG = 1
IBRION = -1
NSW = 0
ISIF = 2
ISPIN = 2
ISYM = 0
LASPH = .TRUE.
ADDGRID = .TRUE.
IVDW = 12
LDIPOL = .TRUE.
IDIPOL = 3
DIPOL = 0.5 0.5 0.5
AMIX = 0.2
BMIX = 0.0001
AMIX_MAG = 0.8
BMIX_MAG = 0.0001
AMIN = 0.01
NELMDL = -12
NELMIN = 4
NELM = 240
LWAVE = .FALSE.
LCHARG = .FALSE.
MAGMOM = {magmom}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-manifest",
        default="review_revision/d3_site_robustness_jobs/manifest.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="review_revision/d3_site_converged_jobs",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def magmom_line(atoms) -> str:
    moments = {"C": 0.1, "Li": 1.0, "Si": 0.1}
    counts: dict[str, int] = {}
    for symbol in atoms.get_chemical_symbols():
        counts[symbol] = counts.get(symbol, 0) + 1
    return " ".join(f"{counts[symbol]}*{moments[symbol]}" for symbol in counts)


def prepare_job(source: Path, target: Path, system: str) -> None:
    target.mkdir(parents=True)
    for name in ("POSCAR", "POTCAR", "KPOINTS"):
        source_file = source / name
        if not source_file.is_file() or source_file.stat().st_size == 0:
            raise FileNotFoundError(source_file)
        shutil.copy2(source_file, target / name)
    atoms = read(target / "POSCAR", format="vasp")
    magmom = magmom_line(atoms)
    (target / "INCAR.stage1").write_text(
        STAGE1_TEMPLATE.format(system=system, magmom=magmom), encoding="utf-8"
    )
    (target / "INCAR.stage2").write_text(
        STAGE2_TEMPLATE.format(system=system, magmom=magmom), encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    source_manifest = Path(args.source_manifest)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.force:
            raise FileExistsError(f"Refusing to replace existing directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    with source_manifest.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    if len(source_rows) != 15:
        raise ValueError(f"Expected frozen 15-site manifest, found {len(source_rows)} rows")
    family_counts = {
        family: sum(row["family"] == family for row in source_rows)
        for family in {row["family"] for row in source_rows}
    }
    if len(family_counts) != 5 or set(family_counts.values()) != {3}:
        raise ValueError(f"Expected five families with three sites each: {family_counts}")
    if any(row["selection_used_mace_predictions"] != "False" for row in source_rows):
        raise ValueError("Site selection manifest is not model blind")

    task_dirs: list[Path] = []
    substrate_dirs: dict[str, Path] = {}
    for row in source_rows:
        family = row["family"]
        if family not in substrate_dirs:
            source = Path(row["substrate_job_dir"])
            target = output_dir / "references" / f"{family}_substrate_d3"
            prepare_job(source, target, f"{family} substrate")
            substrate_dirs[family] = target.resolve()
            task_dirs.append(target.resolve())

    manifest: list[dict[str, str]] = []
    for row in source_rows:
        source = Path(row["job_dir"])
        target = output_dir / "sites" / source.name
        prepare_job(source, target, f"{row['family']} {row['label']}")
        task_dirs.append(target.resolve())
        manifest.append(
            {
                **row,
                "job_dir": str(target.resolve()),
                "substrate_job_dir": str(substrate_dirs[row["family"]]),
                "scf_protocol": "two_stage_pbe_d3_bj_dipole",
            }
        )

    with (output_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    (output_dir / "job_list.txt").write_text(
        "\n".join(str(path) for path in task_dirs) + "\n", encoding="utf-8"
    )
    (output_dir / "DESIGN.md").write_text(
        "# Converged D3 Site Robustness Design\n\n"
        "The 15 site geometries are exactly the frozen, model-blind selection in "
        "the preceding three-sites-per-family manifest. Five matching Li-removed "
        "substrates are recomputed. Each CPU-only calculation first preconverges "
        "PBE-D3(BJ) without the dipole correction, then restarts from WAVECAR and "
        "CHGCAR with the z-directed slab dipole correction and ALGO=All. A final "
        "result is accepted only when the last electronic "
        "iteration is strictly below NELM and all energies and forces are finite. "
        "The isolated-Li reference is the existing 33-iteration converged result.\n",
        encoding="utf-8",
    )
    print(f"Prepared {len(task_dirs)} CPU-only two-stage jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
