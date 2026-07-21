#!/usr/bin/env python3
"""Prepare VASP job folders from generated POSCAR files.

POTCAR files are licensed VASP inputs, so this script only concatenates them
when you provide --potcar-root pointing to your local PAW_PBE potential tree.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from ase.io import read


POTCAR_CHOICES = {
    "C": ("C",),
    "Li": ("Li_sv", "Li"),
    "Si": ("Si",),
}


INCAR_RELAX = """SYSTEM = Li defective graphene MACE training label
ENCUT = 520
EDIFF = 1E-5
EDIFFG = -0.02
ISTART = 0
ICHARG = 2
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = Auto
ALGO = Normal
NCORE = 4

IBRION = 2
NSW = 100
ISIF = 2

ISPIN = 2
ISYM = 0
LASPH = .TRUE.
ADDGRID = .TRUE.
LWAVE = .FALSE.
LCHARG = .FALSE.

NELM = 120
"""


INCAR_SP = """SYSTEM = Li defective graphene MACE training label
ENCUT = 520
EDIFF = 1E-6
ISTART = 0
ICHARG = 2
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = Auto
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

NELM = 120
"""


KPOINTS = """Automatic mesh
0
Gamma
3 3 1
0 0 0
"""


SLURM_TEMPLATE = """#!/usr/bin/env bash
#SBATCH -J vasp-{case}
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks={ntasks}
#SBATCH --cpus-per-task=1
#SBATCH --mem={mem}
#SBATCH --time={time}
#SBATCH --output=vasp-%j.out
#SBATCH --error=vasp-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${{PATH}}"

source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge || true
module load vasp/5.4.1

cd "${{SLURM_SUBMIT_DIR}}"

ulimit -s unlimited
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export I_MPI_DEBUG="${{I_MPI_DEBUG:-0}}"

if [[ ! -s POTCAR ]]; then
    echo "Missing POTCAR in ${{PWD}}. Build it from licensed VASP PAW_PBE potentials." >&2
    exit 1
fi

which vasp_std
srun --mpi=pmi2 vasp_std > vasp.log
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare VASP input directories.")
    parser.add_argument("--structures-dir", default="structures/vasp")
    parser.add_argument("--output-dir", default="dft_outputs")
    parser.add_argument(
        "--mode",
        choices=("relax", "singlepoint"),
        default="relax",
        help="Use relax first unless you intentionally want fixed-geometry labels.",
    )
    parser.add_argument(
        "--potcar-root",
        default=None,
        help="Root containing PAW_PBE element folders, e.g. /path/to/potpaw_PBE.",
    )
    parser.add_argument("--ntasks", type=int, default=16)
    parser.add_argument("--mem", default="16G")
    parser.add_argument("--time", default="12:00:00")
    return parser.parse_args()


def case_name(poscar: Path) -> str:
    name = re.sub(r"^POSCAR_", "", poscar.name)
    return re.sub(r"\.vasp$", "", name)


def element_order(poscar: Path) -> list[str]:
    atoms = read(poscar)
    order: list[str] = []
    for symbol in atoms.get_chemical_symbols():
        if symbol not in order:
            order.append(symbol)
    return order


def element_counts(poscar: Path) -> list[tuple[str, int]]:
    atoms = read(poscar)
    counts: list[tuple[str, int]] = []
    for symbol in atoms.get_chemical_symbols():
        if counts and counts[-1][0] == symbol:
            counts[-1] = (symbol, counts[-1][1] + 1)
        elif symbol in [item[0] for item in counts]:
            for index, (existing, count) in enumerate(counts):
                if existing == symbol:
                    counts[index] = (existing, count + 1)
                    break
        else:
            counts.append((symbol, 1))
    return counts


def magmom_value(symbol: str) -> float:
    if symbol == "Li":
        return 1.0
    if symbol in {"C", "Si"}:
        return 0.1
    return 0.5


def add_magmom(incar: str, counts: list[tuple[str, int]]) -> str:
    magmom = " ".join(f"{count}*{magmom_value(symbol):.1f}" for symbol, count in counts)
    return incar.rstrip() + f"\nMAGMOM = {magmom}\n"


def find_potcar(root: Path, element: str) -> Path:
    choices = POTCAR_CHOICES.get(element, (element,))
    for choice in choices:
        candidate = root / choice / "POTCAR"
        if candidate.is_file():
            return candidate
    tried = ", ".join(str(root / choice / "POTCAR") for choice in choices)
    raise FileNotFoundError(f"Could not find POTCAR for {element}. Tried: {tried}")


def write_potcar(job_dir: Path, root: Path, elements: list[str]) -> None:
    with (job_dir / "POTCAR").open("wb") as handle:
        for element in elements:
            handle.write(find_potcar(root, element).read_bytes())


def write_missing_potcar_note(job_dir: Path, elements: list[str]) -> None:
    parts = [f"/path/to/potpaw_PBE/{element}/POTCAR" for element in elements]
    parts = [
        part.replace("/Li/POTCAR", "/Li_sv/POTCAR") if "/Li/" in part else part
        for part in parts
    ]
    note = [
        "POTCAR was not generated because --potcar-root was not provided.",
        "",
        "Concatenate licensed PAW_PBE potentials in this exact POSCAR order:",
        " ".join(elements),
        "",
        "Recommended choices here: C, Li_sv, Si.",
        "",
        "Example:",
        "cat " + " ".join(parts) + " > POTCAR",
    ]
    (job_dir / "POTCAR_REQUIRED.txt").write_text("\n".join(note) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    structures_dir = Path(args.structures_dir)
    output_dir = Path(args.output_dir)
    potcar_root = Path(args.potcar_root).resolve() if args.potcar_root else None

    poscars = sorted(structures_dir.glob("POSCAR*.vasp"))
    if not poscars:
        raise SystemExit(f"No POSCAR*.vasp files found under {structures_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    incar = INCAR_RELAX if args.mode == "relax" else INCAR_SP

    for poscar in poscars:
        case = case_name(poscar)
        job_dir = output_dir / case
        job_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(poscar, job_dir / "POSCAR")
        counts = element_counts(job_dir / "POSCAR")
        (job_dir / "INCAR").write_text(add_magmom(incar, counts), encoding="utf-8")
        (job_dir / "KPOINTS").write_text(KPOINTS, encoding="utf-8")
        (job_dir / "submit_vasp.slurm").write_text(
            SLURM_TEMPLATE.format(
                case=case,
                ntasks=args.ntasks,
                mem=args.mem,
                time=args.time,
            ),
            encoding="utf-8",
        )
        (job_dir / "submit_vasp.slurm").chmod(0o755)

        elements = element_order(job_dir / "POSCAR")
        if potcar_root:
            write_potcar(job_dir, potcar_root, elements)
            status = "POTCAR written"
        else:
            write_missing_potcar_note(job_dir, elements)
            status = "POTCAR_REQUIRED.txt written"
        print(f"{job_dir}: elements {' '.join(elements)}; {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
