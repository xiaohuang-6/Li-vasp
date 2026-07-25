#!/usr/bin/env python3
"""Prepare VASP CI-NEB job folders from existing Li path endpoints.

This creates review_revision/neb_jobs/<family>_<path_id>/ with 00..NN POSCAR
folders, INCAR, KPOINTS, and a job list. The generated paths are templates from
current endpoint structures; endpoints and final relaxed geometries still need
scientific review before production use.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd
from ase.io import read, write


INCAR_TEMPLATE = """SYSTEM = Li graphene review CI-NEB
ENCUT = 520
EDIFF = 1E-6
EDIFFG = -0.03
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = .FALSE.
ALGO = Normal
NCORE = 2

IBRION = 3
POTIM = 0
NSW = 200
ISIF = 2
IOPT = 1
SPRING = -5
LCLIMB = .TRUE.
IMAGES = {images}

ISPIN = 2
ISYM = 0
LASPH = .TRUE.
ADDGRID = .TRUE.
LWAVE = .FALSE.
LCHARG = .FALSE.
LDIPOL = .TRUE.
IDIPOL = 3
IVDW = 12

NELM = 160
MAGMOM = {magmom}
"""


KPOINTS = """Automatic mesh
0
Gamma
3 3 1
0 0 0
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths-csv", default="results/two_day_rush/path_barriers.csv")
    parser.add_argument("--structures-dir", default="structures/li_sampling")
    parser.add_argument("--output-dir", default="review_revision/neb_jobs")
    parser.add_argument("--images", type=int, default=5, help="Number of intermediate NEB images.")
    parser.add_argument("--potcar-root", default="", help="Optional PAW_PBE root. If omitted, write POTCAR_REQUIRED.txt.")
    return parser.parse_args()


def endpoint_path(structures_dir: Path, family: str, label: str) -> Path:
    return structures_dir / f"POSCAR_SP_{family}_{label}.vasp"


def magmom_for_atoms(atoms) -> str:
    counts = {}
    for sym in atoms.get_chemical_symbols():
        counts[sym] = counts.get(sym, 0) + 1
    parts = []
    if counts.get("C"):
        parts.append(f"{counts['C']}*0.1")
    if counts.get("Li"):
        parts.append(f"{counts['Li']}*1.0")
    if counts.get("Si"):
        parts.append(f"{counts['Si']}*0.1")
    return " ".join(parts)


def write_potcar_note(job_dir: Path, atoms, potcar_root: str) -> None:
    symbols = []
    for sym in atoms.get_chemical_symbols():
        if sym not in symbols:
            symbols.append(sym)
    if potcar_root:
        chunks = []
        for sym in symbols:
            choice = "Li_sv" if sym == "Li" else sym
            potcar = Path(potcar_root) / choice / "POTCAR"
            if not potcar.exists():
                raise FileNotFoundError(f"Missing POTCAR for {sym}: {potcar}")
            chunks.append(potcar.read_bytes())
        (job_dir / "POTCAR").write_bytes(b"".join(chunks))
    else:
        (job_dir / "POTCAR_REQUIRED.txt").write_text(
            "Create POTCAR in this directory using licensed PAW_PBE potentials in this order:\n"
            + " ".join("Li_sv" if sym == "Li" else sym for sym in symbols)
            + "\n",
            encoding="utf-8",
        )


def interpolate_positions(start, end, n_images: int):
    frames = []
    for idx in range(n_images + 2):
        frac = idx / (n_images + 1)
        atoms = start.copy()
        atoms.positions = (1.0 - frac) * start.positions + frac * end.positions
        frames.append(atoms)
    return frames


def main() -> int:
    args = parse_args()
    paths = pd.read_csv(args.paths_csv)
    structures_dir = Path(args.structures_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    job_dirs = []

    for _, row in paths.iterrows():
        family = str(row["family"])
        path_id = str(row["path_id"])
        start_label = str(row["path_start"])
        end_label = str(row["path_end"])
        start_path = endpoint_path(structures_dir, family, start_label)
        end_path = endpoint_path(structures_dir, family, end_label)
        if not start_path.exists() or not end_path.exists():
            print(f"Skipping {family} {path_id}: missing endpoint POSCAR")
            continue
        start = read(start_path)
        end = read(end_path)
        if len(start) != len(end):
            print(f"Skipping {family} {path_id}: endpoint atom counts differ")
            continue
        job_dir = output_dir / f"{family}_{path_id}_{start_label}_to_{end_label}"
        if job_dir.exists():
            shutil.rmtree(job_dir)
        job_dir.mkdir(parents=True)
        frames = interpolate_positions(start, end, args.images)
        for idx, atoms in enumerate(frames):
            img_dir = job_dir / f"{idx:02d}"
            img_dir.mkdir()
            write(img_dir / "POSCAR", atoms, format="vasp", direct=True, sort=False)
        (job_dir / "INCAR").write_text(INCAR_TEMPLATE.format(images=args.images, magmom=magmom_for_atoms(start)), encoding="utf-8")
        (job_dir / "KPOINTS").write_text(KPOINTS, encoding="utf-8")
        write_potcar_note(job_dir, start, args.potcar_root)
        (job_dir / "README.txt").write_text(
            "Review this NEB template before production. Endpoints should ideally be individually relaxed with the same spin/vdW/dipole settings.\n",
            encoding="utf-8",
        )
        job_dirs.append(job_dir)

    list_path = output_dir / "neb_job_list.txt"
    list_path.write_text("\n".join(str(path.resolve()) for path in job_dirs) + "\n", encoding="utf-8")
    print(f"Wrote {len(job_dirs)} NEB job templates")
    print(f"Wrote {list_path}")
    return 0 if job_dirs else 1


if __name__ == "__main__":
    raise SystemExit(main())
