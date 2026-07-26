#!/usr/bin/env python3
"""Prepare low-cost CI-NEB fallback jobs from existing NEB endpoints.

The normal review NEB jobs use 5 intermediate images, ENCUT=520 eV, a 3x3x1
k-point mesh, and a tighter force target. These fallback jobs are intentionally
smaller so they can finish quickly enough to guide a 24-hour manuscript
revision. Treat the output as rapid-review NEB evidence, not as a replacement
for fully converged production barriers.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ase.io import read, write


REPRESENTATIVE_JOBS = (
    "A_Perfect_path01_prior_li_xy_to_hollow_C3",
    "B1_Monovacancy_path01_prior_li_xy_to_bridge_C_C",
    "B2_Divacancy_path02_top_central_C_to_hollow_C3",
    "C_StoneWales_path02_top_central_C_to_top_offset_C",
    "D_SiGraphene_path02_top_central_C_to_hollow_C3",
)


FAST_INCAR_TEMPLATE = """SYSTEM = Li graphene fast review CI-NEB
ENCUT = 400
EDIFF = 1E-5
EDIFFG = -0.08
ISMEAR = 0
SIGMA = 0.05
PREC = Normal
LREAL = Auto
ALGO = Fast
NCORE = 4

IBRION = 3
POTIM = 0
NSW = 80
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
    parser.add_argument("--source-dir", default="review_revision/neb_jobs")
    parser.add_argument("--output-dir", default="review_revision/neb_fast_jobs")
    parser.add_argument("--images", type=int, default=3)
    parser.add_argument(
        "--job",
        action="append",
        default=[],
        help="Specific NEB job directory basename to prepare. Repeatable. Defaults to five representative paths.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove existing output directory first. Do not use on active fast NEB jobs.",
    )
    return parser.parse_args()


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


def endpoint_dirs(source_job: Path) -> tuple[Path, Path]:
    image_dirs = sorted(path for path in source_job.iterdir() if path.is_dir() and path.name.isdigit())
    if len(image_dirs) < 2:
        raise FileNotFoundError(f"{source_job} does not contain numbered endpoint directories")
    return image_dirs[0], image_dirs[-1]


def interpolate(start, end, n_images: int):
    frames = []
    for index in range(n_images + 2):
        frac = index / (n_images + 1)
        atoms = start.copy()
        atoms.positions = (1.0 - frac) * start.positions + frac * end.positions
        frames.append(atoms)
    return frames


def prepare_one(source_job: Path, output_job: Path, images: int) -> None:
    start_dir, end_dir = endpoint_dirs(source_job)
    start = read(start_dir / "POSCAR", format="vasp")
    end = read(end_dir / "POSCAR", format="vasp")
    if len(start) != len(end):
        raise ValueError(f"Endpoint atom counts differ for {source_job.name}")
    output_job.mkdir(parents=True)
    for index, atoms in enumerate(interpolate(start, end, images)):
        image_dir = output_job / f"{index:02d}"
        image_dir.mkdir()
        write(image_dir / "POSCAR", atoms, format="vasp", direct=True, sort=False)
    (output_job / "INCAR").write_text(
        FAST_INCAR_TEMPLATE.format(images=images, magmom=magmom_for_atoms(start)),
        encoding="utf-8",
    )
    (output_job / "KPOINTS").write_text(KPOINTS_FAST, encoding="utf-8")
    for filename in ("POTCAR",):
        source = source_job / filename
        if not source.exists():
            raise FileNotFoundError(f"Missing {source}")
        shutil.copy2(source, output_job / filename)
    (output_job / "README.txt").write_text(
        "Fast 24h fallback CI-NEB: 3 images, Gamma-only, ENCUT=400, EDIFFG=-0.08. "
        "Use only if it converges and the geometry is physically reasonable.\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.force:
            raise FileExistsError(f"{output_dir} exists; pass --force only if no jobs are active there")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    names = args.job or list(REPRESENTATIVE_JOBS)
    job_dirs: list[Path] = []
    for name in names:
        source_job = source_dir / name
        if not source_job.exists():
            print(f"Skipping missing source NEB job: {source_job}")
            continue
        output_job = output_dir / name
        prepare_one(source_job, output_job, args.images)
        job_dirs.append(output_job)

    (output_dir / "neb_fast_job_list.txt").write_text(
        "\n".join(str(path.resolve()) for path in job_dirs) + ("\n" if job_dirs else ""),
        encoding="utf-8",
    )
    print(f"Wrote {len(job_dirs)} fast NEB jobs")
    print(output_dir / "neb_fast_job_list.txt")
    return 0 if job_dirs else 1


if __name__ == "__main__":
    raise SystemExit(main())
