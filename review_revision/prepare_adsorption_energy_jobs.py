#!/usr/bin/env python3
"""Prepare VASP single-point jobs for Li adsorption energies with D3 and dipole correction.

For each relaxed Li+substrate model under dft_outputs/<family>, this script
creates three kinds of jobs:

1. adsorbed: the relaxed Li+substrate structure;
2. substrate: the same structure with Li atoms removed;
3. Li_atom: a single isolated Li atom reference, written once.

The adsorption energy is collected later as
E_ads = E(Li+substrate) - E(substrate) - n_Li * E(Li_atom).
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

from ase import Atoms
from ase.io import read, write


FAMILIES = (
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
)


SLAB_INCAR_TEMPLATE = """SYSTEM = Li adsorption energy {family} {component}
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


LI_ATOM_INCAR = """SYSTEM = Li isolated atom reference
ENCUT = 520
EDIFF = 1E-7
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = .FALSE.
ALGO = Normal
NCORE = 1

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
MAGMOM = 1*1.0
"""


KPOINTS_SLAB = """Automatic mesh
0
Gamma
3 3 1
0 0 0
"""


KPOINTS_ATOM = """Automatic mesh
0
Gamma
1 1 1
0 0 0
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dft-root", default="dft_outputs")
    parser.add_argument("--output-dir", default="review_revision/adsorption_energy_jobs")
    parser.add_argument(
        "--families",
        nargs="*",
        default=list(FAMILIES),
        help="Families to prepare. Defaults to all five current systems.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove an existing output directory before writing. Do not use on active jobs.",
    )
    return parser.parse_args()


def read_source_structure(case_dir: Path):
    for name in ("CONTCAR", "POSCAR"):
        path = case_dir / name
        if path.exists() and path.stat().st_size > 0:
            return read(path, format="vasp"), path
    raise FileNotFoundError(f"Missing CONTCAR/POSCAR under {case_dir}")


def magmom_for_atoms(atoms) -> str:
    counts: dict[str, int] = {}
    for symbol in atoms.get_chemical_symbols():
        counts[symbol] = counts.get(symbol, 0) + 1
    values = []
    for symbol in sorted(counts):
        moment = 1.0 if symbol == "Li" else 0.1
        values.append(f"{counts[symbol]}*{moment}")
    return " ".join(values)


def ordered_symbols_for_vasp_sort(atoms) -> list[str]:
    return sorted(set(atoms.get_chemical_symbols()))


def split_potcar(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    marker = b"End of Dataset"
    chunks: dict[str, bytes] = {}
    start = 0
    while True:
        index = data.find(marker, start)
        if index == -1:
            break
        end = data.find(b"\n", index)
        if end == -1:
            end = index + len(marker)
        chunk = data[start : end + 1]
        start = end + 1
        match = re.search(rb"TITEL\s*=\s*PAW_PBE\s+([A-Za-z0-9_]+)", chunk)
        if not match:
            continue
        potcar_name = match.group(1).decode("ascii", errors="ignore")
        symbol = re.match(r"([A-Za-z]+)", potcar_name).group(1)  # type: ignore[union-attr]
        chunks[symbol] = chunk
    if not chunks:
        raise ValueError(f"No POTCAR chunks parsed from {path}")
    return chunks


def write_potcar(job_dir: Path, source_potcar: Path, symbols: list[str]) -> str:
    chunks = split_potcar(source_potcar)
    missing = [symbol for symbol in symbols if symbol not in chunks]
    if missing:
        raise FileNotFoundError(f"{source_potcar} lacks POTCAR chunks for: {', '.join(missing)}")
    (job_dir / "POTCAR").write_bytes(b"".join(chunks[symbol] for symbol in symbols))
    return str(source_potcar)


def write_job(job_dir: Path, atoms, incar: str, kpoints: str, source_potcar: Path) -> str:
    job_dir.mkdir(parents=True, exist_ok=True)
    write(job_dir / "POSCAR", atoms, format="vasp", direct=True, sort=True)
    (job_dir / "INCAR").write_text(incar, encoding="utf-8")
    (job_dir / "KPOINTS").write_text(kpoints, encoding="utf-8")
    return write_potcar(job_dir, source_potcar, ordered_symbols_for_vasp_sort(atoms))


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


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        if not args.force:
            raise FileExistsError(f"{output_dir} exists; pass --force only if no jobs are active there")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    dft_root = Path(args.dft_root)
    manifest_rows: list[dict[str, object]] = []
    job_dirs: list[Path] = []
    li_source_potcar: Path | None = None

    for family in args.families:
        case_dir = dft_root / family
        atoms, structure_source = read_source_structure(case_dir)
        source_potcar = case_dir / "POTCAR"
        if not source_potcar.exists():
            raise FileNotFoundError(f"Missing source POTCAR: {source_potcar}")
        if "Li" in atoms.get_chemical_symbols():
            li_source_potcar = source_potcar

        n_li = atoms.get_chemical_symbols().count("Li")
        if n_li < 1:
            raise ValueError(f"{family} source structure has no Li atom")

        ads_dir = output_dir / f"{family}_adsorbed_sp"
        potcar_source = write_job(
            ads_dir,
            atoms,
            SLAB_INCAR_TEMPLATE.format(family=family, component="adsorbed", magmom=magmom_for_atoms(atoms)),
            KPOINTS_SLAB,
            source_potcar,
        )
        job_dirs.append(ads_dir)
        manifest_rows.append(
            {
                "job_dir": str(ads_dir.resolve()),
                "family": family,
                "component": "adsorbed",
                "n_li": n_li,
                "natoms": len(atoms),
                "structure_source": str(structure_source),
                "potcar_source": potcar_source,
            }
        )

        substrate = atoms[[index for index, symbol in enumerate(atoms.get_chemical_symbols()) if symbol != "Li"]]
        sub_dir = output_dir / f"{family}_substrate_sp"
        potcar_source = write_job(
            sub_dir,
            substrate,
            SLAB_INCAR_TEMPLATE.format(family=family, component="substrate", magmom=magmom_for_atoms(substrate)),
            KPOINTS_SLAB,
            source_potcar,
        )
        job_dirs.append(sub_dir)
        manifest_rows.append(
            {
                "job_dir": str(sub_dir.resolve()),
                "family": family,
                "component": "substrate",
                "n_li": 0,
                "natoms": len(substrate),
                "structure_source": str(structure_source),
                "potcar_source": potcar_source,
            }
        )

    if li_source_potcar is None:
        raise ValueError("Could not find a source POTCAR containing Li")
    li_atom = Atoms("Li", positions=[(10.0, 10.0, 10.0)], cell=[20.0, 20.0, 20.0], pbc=True)
    li_dir = output_dir / "Li_atom_sp"
    potcar_source = write_job(li_dir, li_atom, LI_ATOM_INCAR, KPOINTS_ATOM, li_source_potcar)
    job_dirs.append(li_dir)
    manifest_rows.append(
        {
            "job_dir": str(li_dir.resolve()),
            "family": "Li_atom",
            "component": "li_atom",
            "n_li": 1,
            "natoms": 1,
            "structure_source": "generated 20 A cubic cell",
            "potcar_source": potcar_source,
        }
    )

    (output_dir / "adsorption_job_list.txt").write_text(
        "\n".join(str(path.resolve()) for path in job_dirs) + "\n",
        encoding="utf-8",
    )
    write_csv(output_dir / "adsorption_manifest.csv", manifest_rows)
    (output_dir / "README.md").write_text(
        "# Adsorption Energy Jobs\n\n"
        "Run these VASP single-point jobs to compute E_ads = E(Li+substrate) - "
        "E(substrate) - n_Li E(Li_atom). Slab jobs use PBE-D3 (IVDW=12) and "
        "IDIPOL=3 dipole correction.\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(job_dirs)} adsorption-energy jobs")
    print(output_dir / "adsorption_job_list.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
