#!/usr/bin/env python3
"""Build small Li/graphene VASP starting structures for DFT labeling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from ase import Atom
from ase.build import graphene
from ase.io import write


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Li/graphene defect structures as VASP POSCAR files."
    )
    parser.add_argument("--output-dir", default="structures/vasp")
    parser.add_argument("--a", type=float, default=2.46, help="Graphene lattice a.")
    parser.add_argument(
        "--supercell",
        nargs=3,
        type=int,
        default=(5, 5, 1),
        metavar=("NX", "NY", "NZ"),
    )
    parser.add_argument("--vacuum", type=float, default=15.0)
    parser.add_argument("--li-height", type=float, default=1.7)
    return parser.parse_args()


def get_z_center(atoms) -> float:
    return float(atoms.positions[:, 2].mean())


def make_graphene(args: argparse.Namespace):
    atoms = graphene(
        formula="C2",
        a=args.a,
        size=tuple(args.supercell),
        vacuum=args.vacuum,
    )
    atoms.pbc = (True, True, True)
    return atoms


def write_poscar(output_dir: Path, filename: str, atoms) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    write(path, atoms, format="vasp", vasp5=True, direct=True, sort=True)
    return {
        "file": str(path),
        "formula": atoms.get_chemical_formula(),
        "natoms": len(atoms),
        "cell": atoms.cell.array.round(8).tolist(),
    }


def build_structure_a(args: argparse.Namespace, output_dir: Path) -> dict[str, object]:
    atoms = make_graphene(args)
    center_x = atoms.cell[0, 0] / 2.0
    center_y = atoms.cell[1, 1] / 2.0
    atoms.append(
        Atom("Li", position=(center_x, center_y, get_z_center(atoms) + args.li_height))
    )
    return write_poscar(output_dir, "POSCAR_A_Perfect.vasp", atoms)


def build_structure_b(args: argparse.Namespace, output_dir: Path) -> list[dict[str, object]]:
    results = []

    atoms_sv = make_graphene(args)
    center = np.array(
        [atoms_sv.cell[0, 0] / 2, atoms_sv.cell[1, 1] / 2, get_z_center(atoms_sv)]
    )
    central_idx = int(np.argmin(np.linalg.norm(atoms_sv.positions - center, axis=1)))
    del atoms_sv[central_idx]
    atoms_sv.append(
        Atom("Li", position=(float(center[0]), float(center[1]), float(center[2] + args.li_height)))
    )
    results.append(write_poscar(output_dir, "POSCAR_B1_Monovacancy.vasp", atoms_sv))

    atoms_dv = make_graphene(args)
    center = np.array(
        [atoms_dv.cell[0, 0] / 2, atoms_dv.cell[1, 1] / 2, get_z_center(atoms_dv)]
    )
    idx1 = int(np.argmin(np.linalg.norm(atoms_dv.positions - center, axis=1)))
    distances = np.linalg.norm(atoms_dv.positions - atoms_dv.positions[idx1], axis=1)
    idx2 = int(np.argsort(distances)[1])
    for index in sorted([idx1, idx2], reverse=True):
        del atoms_dv[index]
    atoms_dv.append(
        Atom("Li", position=(float(center[0]), float(center[1]), float(center[2] + args.li_height)))
    )
    results.append(write_poscar(output_dir, "POSCAR_B2_Divacancy.vasp", atoms_dv))
    return results


def build_structure_c(args: argparse.Namespace, output_dir: Path) -> dict[str, object]:
    atoms_sw = make_graphene(args)
    center = np.array(
        [atoms_sw.cell[0, 0] / 2, atoms_sw.cell[1, 1] / 2, get_z_center(atoms_sw)]
    )
    idx1 = int(np.argmin(np.linalg.norm(atoms_sw.positions - center, axis=1)))
    distances = np.linalg.norm(atoms_sw.positions - atoms_sw.positions[idx1], axis=1)
    idx2 = int(np.argsort(distances)[1])
    midpoint = (atoms_sw.positions[idx1] + atoms_sw.positions[idx2]) / 2.0

    # Rotate the selected C-C pair by 90 degrees around its midpoint. This is a
    # reproducible unrelaxed Stone-Wales starting geometry for subsequent DFT.
    for index in [idx1, idx2]:
        x, y, z = atoms_sw.positions[index]
        atoms_sw.positions[index] = [
            -(y - midpoint[1]) + midpoint[0],
            (x - midpoint[0]) + midpoint[1],
            z,
        ]
    atoms_sw.append(
        Atom(
            "Li",
            position=(
                float(midpoint[0]),
                float(midpoint[1]),
                float(midpoint[2] + args.li_height),
            ),
        )
    )
    return write_poscar(output_dir, "POSCAR_C_StoneWales.vasp", atoms_sw)


def build_structure_d(args: argparse.Namespace, output_dir: Path) -> dict[str, object]:
    atoms_si = make_graphene(args)
    center = np.array(
        [atoms_si.cell[0, 0] / 2, atoms_si.cell[1, 1] / 2, get_z_center(atoms_si)]
    )
    d_si = 2.35 / np.sqrt(3)
    si_positions = [
        [center[0], center[1], center[2] + 2.0],
        [center[0] + d_si, center[1] + d_si, center[2] + 2.0 + d_si * np.sqrt(2)],
        [center[0] - d_si, center[1] - d_si, center[2] + 2.0 + d_si * np.sqrt(2)],
        [center[0] - d_si, center[1] + d_si, center[2] + 2.0 + d_si * np.sqrt(2)],
    ]
    for position in si_positions:
        atoms_si.append(Atom("Si", position=position))
    atoms_si.append(
        Atom("Li", position=[center[0] + 1.5, center[1], center[2] + 1.5])
    )
    return write_poscar(output_dir, "POSCAR_D_SiGraphene.vasp", atoms_si)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)

    records: list[dict[str, object]] = []
    records.append(build_structure_a(args, output_dir))
    records.extend(build_structure_b(args, output_dir))
    records.append(build_structure_c(args, output_dir))
    records.append(build_structure_d(args, output_dir))

    summary = output_dir / "structure_summary.json"
    summary.write_text(json.dumps(records, indent=2), encoding="utf-8")
    for record in records:
        print(f"{record['file']}: {record['formula']} ({record['natoms']} atoms)")
    print(f"Wrote {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
