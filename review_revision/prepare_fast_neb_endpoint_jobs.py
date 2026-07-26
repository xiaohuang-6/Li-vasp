#!/usr/bin/env python3
"""Prepare endpoint single-point jobs matching the fast CI-NEB settings."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from ase.io import read, write


ENDPOINT_INCAR = """SYSTEM = Fast NEB endpoint single point
ENCUT = 400
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
PREC = Normal
LREAL = Auto
ALGO = Fast
NCORE = 4

IBRION = -1
NSW = 0
ISIF = 2

ISPIN = 2
ISYM = 0
LASPH = .TRUE.
ADDGRID = .TRUE.
LWAVE = .FALSE.
LCHARG = .FALSE.
LDIPOL = .TRUE.
IDIPOL = 3
IVDW = 12

NELM = 100
MAGMOM = {magmom}
"""


KPOINTS_FAST = """Automatic mesh
0
Gamma
1 1 1
0 0 0
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neb-job-list", default="review_revision/neb_fast_jobs/neb_fast_job_list.txt")
    parser.add_argument("--output-dir", default="review_revision/neb_fast_endpoint_jobs")
    parser.add_argument("--force", action="store_true", help="Remove existing endpoint job directory before writing.")
    return parser.parse_args()


def read_job_dirs(path: Path) -> list[Path]:
    return [Path(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def magmom_for_atoms(atoms) -> str:
    counts: dict[str, int] = {}
    for sym in atoms.get_chemical_symbols():
        counts[sym] = counts.get(sym, 0) + 1
    parts: list[str] = []
    if counts.get("C"):
        parts.append(f"{counts['C']}*0.1")
    if counts.get("Li"):
        parts.append(f"{counts['Li']}*1.0")
    if counts.get("Si"):
        parts.append(f"{counts['Si']}*0.1")
    return " ".join(parts)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def endpoint_indices(neb_job: Path) -> tuple[int, int]:
    image_dirs = sorted(int(path.name) for path in neb_job.iterdir() if path.is_dir() and path.name.isdigit())
    if len(image_dirs) < 2:
        raise FileNotFoundError(f"{neb_job} lacks numbered endpoint directories")
    return image_dirs[0], image_dirs[-1]


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.force:
            raise FileExistsError(f"{output_dir} exists; pass --force only if no endpoint jobs are active")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    rows: list[dict[str, object]] = []
    job_dirs: list[Path] = []
    for neb_job in read_job_dirs(Path(args.neb_job_list)):
        start_idx, end_idx = endpoint_indices(neb_job)
        for image_index in (start_idx, end_idx):
            atoms = read(neb_job / f"{image_index:02d}" / "POSCAR", format="vasp")
            job_dir = output_dir / f"{neb_job.name}_image{image_index:02d}_sp"
            job_dir.mkdir(parents=True)
            write(job_dir / "POSCAR", atoms, format="vasp", direct=True, sort=False)
            (job_dir / "INCAR").write_text(
                ENDPOINT_INCAR.format(magmom=magmom_for_atoms(atoms)),
                encoding="utf-8",
            )
            (job_dir / "KPOINTS").write_text(KPOINTS_FAST, encoding="utf-8")
            shutil.copy2(neb_job / "POTCAR", job_dir / "POTCAR")
            job_dirs.append(job_dir)
            rows.append(
                {
                    "job_dir": str(job_dir.resolve()),
                    "parent_job": neb_job.name,
                    "image_index": image_index,
                    "source_poscar": str((neb_job / f"{image_index:02d}" / "POSCAR").resolve()),
                    "natoms": len(atoms),
                }
            )

    (output_dir / "endpoint_job_list.txt").write_text(
        "\n".join(str(path.resolve()) for path in job_dirs) + ("\n" if job_dirs else ""),
        encoding="utf-8",
    )
    write_csv(output_dir / "endpoint_manifest.csv", rows)
    print(f"Wrote {len(job_dirs)} fast NEB endpoint SP jobs")
    print(output_dir / "endpoint_job_list.txt")
    return 0 if job_dirs else 1


if __name__ == "__main__":
    raise SystemExit(main())
