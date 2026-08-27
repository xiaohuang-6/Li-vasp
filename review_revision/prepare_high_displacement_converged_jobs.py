#!/usr/bin/env python3
"""Prepare stable-SCF outputs for the nine high-displacement snapshots."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

from ase.io import read


INCAR_TEMPLATE = """SYSTEM = high-displacement SCF {stage} {case}
ENCUT = 520
EDIFF = {ediff}
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = .FALSE.
ALGO = All
TIME = 0.2
NCORE = 4
ISTART = {istart}
ICHARG = {icharg}
IBRION = -1
NSW = 0
ISIF = 2
ISPIN = 2
ISYM = 0
LASPH = .TRUE.
ADDGRID = .TRUE.
AMIX = 0.2
BMIX = 0.0001
AMIX_MAG = 0.8
BMIX_MAG = 0.0001
AMIN = 0.01
NELMDL = -8
NELMIN = 4
NELM = {nelm}
LWAVE = {lwave}
LCHARG = {lcharg}
MAGMOM = {magmom}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-manifest",
        default="review_revision/md_snapshot_dft_jobs/md_snapshot_dft_manifest.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="review_revision/high_displacement_converged_jobs",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def strict_scf_converged(job_dir: Path) -> bool:
    outcar = job_dir / "OUTCAR"
    oszicar = job_dir / "OSZICAR"
    if not outcar.is_file() or not oszicar.is_file():
        return False
    outcar_text = outcar.read_text(encoding="utf-8", errors="replace")
    oszicar_text = oszicar.read_text(encoding="utf-8", errors="replace")
    iterations = [
        int(value)
        for value in re.findall(
            r"^\s*(?:DAV|RMM|SDA|CGA|CG|DMP|DIA|EIG)\s*:\s*(\d+)",
            oszicar_text,
            re.MULTILINE,
        )
    ]
    nelm_matches = re.findall(r"\bNELM\s*=\s*(\d+)", outcar_text)
    return bool(
        "General timing and accounting informations for this job" in outcar_text
        and "aborting loop because EDIFF is reached" in outcar_text
        and iterations
        and nelm_matches
        and iterations[-1] < int(nelm_matches[-1])
    )


def magmom_line(atoms) -> str:
    moments = {"C": 0.1, "Li": 1.0, "Si": 0.1}
    counts: dict[str, int] = {}
    for symbol in atoms.get_chemical_symbols():
        counts[symbol] = counts.get(symbol, 0) + 1
    return " ".join(f"{counts[symbol]}*{moments[symbol]}" for symbol in counts)


def prepare_job(source: Path, target: Path, case: str) -> None:
    target.mkdir(parents=True)
    for name in ("POSCAR", "POTCAR", "KPOINTS"):
        source_file = source / name
        if not source_file.is_file() or source_file.stat().st_size == 0:
            raise FileNotFoundError(source_file)
        shutil.copy2(source_file, target / name)
    magmom = magmom_line(read(target / "POSCAR", format="vasp"))
    (target / "INCAR.stage1").write_text(
        INCAR_TEMPLATE.format(
            stage="precondition",
            case=case,
            ediff="1E-4",
            istart=0,
            icharg=2,
            nelm=180,
            lwave=".TRUE.",
            lcharg=".TRUE.",
            magmom=magmom,
        ),
        encoding="utf-8",
    )
    (target / "INCAR.stage2").write_text(
        INCAR_TEMPLATE.format(
            stage="final",
            case=case,
            ediff="1E-6",
            istart=1,
            icharg=1,
            nelm=240,
            lwave=".FALSE.",
            lcharg=".FALSE.",
            magmom=magmom,
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.force:
            raise FileExistsError(f"Refusing to replace existing directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    with Path(args.source_manifest).open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    if len(source_rows) != 9:
        raise ValueError(f"Expected nine high-displacement snapshots, found {len(source_rows)}")

    retry_rows: list[dict[str, str]] = []
    combined_rows: list[dict[str, str]] = []
    job_dirs: list[Path] = []
    for row in source_rows:
        source = Path(row["job_dir"])
        if strict_scf_converged(source):
            combined_rows.append({**row, "scf_provenance": "strict_original"})
            continue
        target = output_dir / "jobs" / source.name
        prepare_job(source, target, row["case"])
        updated = {
            **row,
            "job_dir": str(target.resolve()),
            "scf_provenance": "two_stage_algo_all_rerun",
        }
        retry_rows.append(updated)
        combined_rows.append(updated)
        job_dirs.append(target.resolve())

    if len(retry_rows) != 4 or len(combined_rows) != 9:
        raise ValueError(
            f"Expected four reruns and nine combined rows; found "
            f"{len(retry_rows)} and {len(combined_rows)}"
        )
    if sum(row["case"] == "B1_Monovacancy" for row in retry_rows) != 3:
        raise ValueError("Expected all three monovacancy snapshots in the rerun set")

    for name, rows in (
        ("retry_manifest.csv", retry_rows),
        ("combined_manifest.csv", combined_rows),
    ):
        with (output_dir / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (output_dir / "job_list.txt").write_text(
        "\n".join(str(path) for path in job_dirs) + "\n", encoding="utf-8"
    )
    (output_dir / "DESIGN.md").write_text(
        "# High-displacement DFT strict-SCF design\n\n"
        "The geometries and model-blind selection of the nine preselected snapshots "
        "are unchanged. Four frames use a CPU-only two-stage ALGO=All protocol: a "
        "1e-4 eV preconditioning stage followed by a restart at 1e-6 eV. Five "
        "frames retain their original strict-SCF outputs. The final nine-row "
        "manifest is accepted only when every output has normal termination, no "
        "fatal marker, finite energy and forces, and last_iter < NELM. Only this "
        "strictly converged set is used for force-error evaluation.\n",
        encoding="utf-8",
    )
    print(f"Prepared {len(retry_rows)} reruns; combined manifest has {len(combined_rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
