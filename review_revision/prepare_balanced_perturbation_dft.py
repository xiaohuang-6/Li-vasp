#!/usr/bin/env python3
"""Prepare a model-independent, family-balanced DFT force benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path

import numpy as np
from ase.io import read, write


FAMILIES = (
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
)

# Per-coordinate Gaussian displacement amplitudes. Replicates are fixed before
# any MACE evaluation so benchmark membership cannot depend on model error.
PERTURBATIONS = (
    (0.03, 1),
    (0.06, 1),
    (0.06, 2),
    (0.10, 1),
    (0.10, 2),
)

INCAR_TEMPLATE = """SYSTEM = balanced independent perturbation force benchmark
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
LWAVE = .FALSE.
LCHARG = .FALSE.

NELM = 180
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
    parser.add_argument("--source-root", default="dft_outputs")
    parser.add_argument(
        "--output-dir",
        default="review_revision/balanced_perturbation_dft_jobs",
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def magmom_line(atoms) -> str:
    moments = {"C": 0.1, "Li": 1.0, "Si": 0.1}
    counts: dict[str, int] = {}
    for symbol in sorted(atoms.get_chemical_symbols()):
        counts[symbol] = counts.get(symbol, 0) + 1
    return " ".join(f"{counts[symbol]}*{moments[symbol]}" for symbol in counts)


def minimum_distance(atoms) -> float:
    distances = atoms.get_all_distances(mic=True)
    distances[np.diag_indices_from(distances)] = np.inf
    return float(np.min(distances))


def generate_perturbation(base, sigma: float, base_seed: int):
    """Deterministically resample until the geometry clears a contact screen."""
    for attempt in range(1000):
        seed = base_seed + attempt * 100_000
        rng = np.random.default_rng(seed)
        displacement = rng.normal(0.0, sigma, size=(len(base), 3))
        displacement -= displacement.mean(axis=0, keepdims=True)
        atoms = base.copy()
        atoms.positions += displacement
        atoms.wrap()
        min_distance = minimum_distance(atoms)
        if min_distance >= 1.15:
            return atoms, displacement, min_distance, seed, attempt
    raise RuntimeError(
        f"Could not generate a geometry with minimum distance >= 1.15 A "
        f"for sigma={sigma} after 1000 attempts"
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root)
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.force:
            raise FileExistsError(f"Refusing to replace existing directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    rows: list[dict[str, object]] = []
    job_dirs: list[Path] = []
    for family_index, family in enumerate(FAMILIES):
        source_dir = source_root / family
        source_structure = source_dir / "CONTCAR"
        source_potcar = source_dir / "POTCAR"
        if not source_structure.is_file() or not source_potcar.is_file():
            raise FileNotFoundError(f"Missing CONTCAR or POTCAR for {family}")
        base = read(source_structure, format="vasp")
        base.calc = None

        for sigma, replicate in PERTURBATIONS:
            base_seed = (
                2026082500
                + family_index * 100
                + int(round(sigma * 100)) * 10
                + replicate
            )
            atoms, displacement, min_distance, seed, attempt = generate_perturbation(
                base, sigma, base_seed
            )

            sigma_tag = f"{int(round(sigma * 100)):02d}"
            job_dir = output_dir / f"{family}_s{sigma_tag}_r{replicate}"
            job_dir.mkdir()
            write(job_dir / "POSCAR", atoms, format="vasp", direct=True, sort=True)
            (job_dir / "INCAR").write_text(
                INCAR_TEMPLATE.format(magmom=magmom_line(atoms)), encoding="utf-8"
            )
            (job_dir / "KPOINTS").write_text(KPOINTS, encoding="utf-8")
            shutil.copy2(source_potcar, job_dir / "POTCAR")

            actual_rms = float(np.sqrt(np.mean(displacement * displacement)))
            atom_rms = float(np.sqrt(np.mean(np.sum(displacement * displacement, axis=1))))
            job_dirs.append(job_dir.resolve())
            rows.append(
                {
                    "job_dir": str(job_dir.resolve()),
                    "family": family,
                    "case": family,
                    "sigma_a": sigma,
                    "replicate": replicate,
                    "seed": seed,
                    "generation_attempt": attempt,
                    "natoms": len(atoms),
                    "formula": atoms.get_chemical_formula(),
                    "actual_component_rms_a": f"{actual_rms:.8f}",
                    "actual_atom_rms_a": f"{atom_rms:.8f}",
                    "max_displacement_a": f"{np.max(np.linalg.norm(displacement, axis=1)):.8f}",
                    "minimum_pair_distance_a": f"{min_distance:.8f}",
                    "source_structure": str(source_structure),
                    "source_structure_sha256": sha256(source_structure),
                    "poscar_sha256": sha256(job_dir / "POSCAR"),
                    "selection_used_model_predictions": False,
                }
            )

    write_csv(output_dir / "manifest.csv", rows)
    (output_dir / "job_list.txt").write_text(
        "\n".join(str(path) for path in job_dirs) + "\n", encoding="utf-8"
    )
    (output_dir / "DESIGN.md").write_text(
        "# Balanced Perturbation Force Benchmark\n\n"
        "This benchmark contains five configurations for each of five chemical families. "
        "Configurations were generated from converged DFT structures using fixed Gaussian "
        "displacement amplitudes and deterministic seeds. Membership was fixed before any "
        "MACE prediction, so model error did not influence selection. DFT single points use "
        "spin-polarized PBE, ENCUT=520 eV, a 3x3x1 mesh, and EDIFF=1e-6 eV.\n",
        encoding="utf-8",
    )
    print(f"Prepared {len(rows)} jobs in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
