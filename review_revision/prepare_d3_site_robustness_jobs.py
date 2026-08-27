#!/usr/bin/env python3
"""Prepare PBE-D3(BJ)+dipole checks for three PBE-ranked sites per family."""

from __future__ import annotations

import argparse
import csv
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np
from ase.io import read


FAMILIES = (
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
)


INCAR_TEMPLATE = """SYSTEM = D3 site robustness {family} {label}
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
LDIPOL = .TRUE.
IDIPOL = 3
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
    parser.add_argument(
        "--site-csv", default="submission_data/results/fixed_site_energies.csv"
    )
    parser.add_argument(
        "--output-dir", default="review_revision/d3_site_robustness_jobs"
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def magmom_line(atoms) -> str:
    moments = {"C": 0.1, "Li": 1.0, "Si": 0.1}
    counts: dict[str, int] = {}
    for symbol in atoms.get_chemical_symbols():
        counts[symbol] = counts.get(symbol, 0) + 1
    return " ".join(f"{counts[s]}*{moments[s]}" for s in counts)


def substrate_only(atoms):
    li_indices = [index for index, atom in enumerate(atoms) if atom.symbol == "Li"]
    if len(li_indices) > 1:
        raise ValueError(f"Expected zero or one Li atom, found {len(li_indices)}")
    substrate = atoms.copy()
    if li_indices:
        del substrate[li_indices[0]]
    return substrate


def same_periodic_geometry(reference, candidate, tolerance: float = 1e-6) -> bool:
    if (
        reference.get_chemical_formula() != candidate.get_chemical_formula()
        or not np.allclose(reference.cell.array, candidate.cell.array, atol=1e-10, rtol=0.0)
    ):
        return False
    cell = np.asarray(reference.cell.array, dtype=float)
    ref_fractional = np.asarray(reference.get_scaled_positions(wrap=True), dtype=float)
    candidate_fractional = np.asarray(candidate.get_scaled_positions(wrap=True), dtype=float)
    ref_symbols = np.asarray(reference.get_chemical_symbols())
    candidate_symbols = np.asarray(candidate.get_chemical_symbols())
    for symbol in sorted(set(ref_symbols)):
        available = list(np.flatnonzero(candidate_symbols == symbol))
        for ref_index in np.flatnonzero(ref_symbols == symbol):
            delta = candidate_fractional[available] - ref_fractional[ref_index]
            delta -= np.rint(delta)
            distances = np.linalg.norm(delta @ cell, axis=1)
            match = int(np.argmin(distances))
            if distances[match] > tolerance:
                return False
            available.pop(match)
    return True


def validate_common_substrate(
    site_paths: list[Path], reference_path: Path, family: str
) -> None:
    reference = substrate_only(read(reference_path, format="vasp"))
    candidates = [
        substrate_only(read(path, format="vasp"))
        for path in site_paths
    ]
    if any(not same_periodic_geometry(reference, item) for item in candidates):
        raise ValueError(
            f"Selected sites do not match the D3 substrate reference geometry: {family}"
        )


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.force:
            raise FileExistsError(f"Refusing to replace existing directory: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    with Path(args.site_csv).open(newline="", encoding="utf-8") as handle:
        sites = list(csv.DictReader(handle))
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sites:
        if row.get("kind") == "site":
            grouped[row["family"]].append(row)
    if set(grouped) != set(FAMILIES):
        raise ValueError(f"Expected site rows for exactly {FAMILIES}; found {sorted(grouped)}")

    selected: list[dict[str, str]] = []
    for family in FAMILIES:
        rows = grouped[family]
        if len(rows) < 3:
            raise ValueError(f"Need at least three fixed sites for {family}")
        family_selection = sorted(rows, key=lambda row: float(row["energy_ev"]))[:3]
        validate_common_substrate(
            [Path(row["path"]) / "POSCAR" for row in family_selection],
            Path("review_revision/adsorption_energy_jobs")
            / f"{family}_substrate_sp/POSCAR",
            family,
        )
        selected.extend(family_selection)

    manifest: list[dict[str, object]] = []
    job_dirs: list[Path] = []
    for site in selected:
        family = site["family"]
        label = site["label"]
        source_poscar = Path(site["path"]) / "POSCAR"
        substrate_job = Path("review_revision/adsorption_energy_jobs") / f"{family}_substrate_sp"
        li_atom_job = Path("review_revision/adsorption_energy_jobs/Li_atom_sp")
        job_dir = output_dir / f"{site['case']}_d3"
        job_dir.mkdir()
        atoms = read(source_poscar, format="vasp")
        shutil.copy2(source_poscar, job_dir / "POSCAR")
        shutil.copy2(Path("dft_outputs") / family / "POTCAR", job_dir / "POTCAR")
        (job_dir / "INCAR").write_text(
            INCAR_TEMPLATE.format(
                family=family, label=label, magmom=magmom_line(atoms)
            ),
            encoding="utf-8",
        )
        (job_dir / "KPOINTS").write_text(KPOINTS, encoding="utf-8")
        job_dirs.append(job_dir.resolve())

        family_rows = sorted(grouped[family], key=lambda row: float(row["energy_ev"]))
        pbe_rank = next(i for i, row in enumerate(family_rows, start=1) if row["case"] == site["case"])
        manifest.append(
            {
                "job_dir": str(job_dir.resolve()),
                "family": family,
                "case": site["case"],
                "label": label,
                "pbe_fixed_site_rank": pbe_rank,
                "pbe_energy_ev": site["energy_ev"],
                "pbe_relative_to_family_site_min_ev": site["rel_to_site_min_ev"],
                "natoms": site["natoms"],
                "formula": site["formula"],
                "source_poscar": str(source_poscar),
                "reused_existing_d3_result": False,
                "substrate_job_dir": str(substrate_job.resolve()),
                "li_atom_job_dir": str(li_atom_job.resolve()),
                "selection_used_mace_predictions": False,
            }
        )

    with (output_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    (output_dir / "job_list.txt").write_text(
        "\n".join(str(path) for path in job_dirs) + "\n", encoding="utf-8"
    )
    (output_dir / "DESIGN.md").write_text(
        "# D3 Site Robustness Design\n\n"
        "For each chemical family, the three lowest-energy placements from the "
        "existing PBE fixed-site scan were selected before the new calculations. "
        "Each selected geometry receives a PBE-D3(BJ) single point with a slab "
        "dipole correction. The substrate coordinates are identical within a family, "
        "so the existing family-specific substrate reference is reused. These are "
        "multi-site fixed-geometry checks, not relaxed adsorption-site searches.\n",
        encoding="utf-8",
    )
    print(f"Selected {len(manifest)} sites; prepared {len(job_dirs)} new jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
