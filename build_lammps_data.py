#!/usr/bin/env python3
"""Build a larger atomic LAMMPS data file from an optimized small structure."""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import numpy as np
from ase import Atoms
from ase.io import read, write
from ase.io.lammpsdata import write_lammps_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replicate an optimized slab and write atomic LAMMPS data."
    )
    parser.add_argument(
        "--input",
        default="structures/optimized/CONTCAR",
        help="Optimized POSCAR/CONTCAR/extxyz input.",
    )
    parser.add_argument("--output", default="data/lammps/defective_graphene.data")
    parser.add_argument(
        "--repeat",
        nargs=3,
        type=int,
        default=(10, 10, 1),
        metavar=("NX", "NY", "NZ"),
        help="Replicate in x/y and stack layers in z. Default keeps a single slab.",
    )
    parser.add_argument(
        "--stack-spacing",
        type=float,
        default=3.35,
        help="Interlayer spacing used when repeat NZ > 1.",
    )
    parser.add_argument(
        "--vacuum",
        type=float,
        default=20.0,
        help="Vacuum added above the final stacked slab along z.",
    )
    parser.add_argument(
        "--specorder",
        nargs="+",
        default=["C", "Li", "Si"],
        help="LAMMPS atom type order. Must match pair_coeff element order.",
    )
    parser.add_argument("--summary", default=None)
    return parser.parse_args()


def stack_z(base: Atoms, nz: int, spacing: float, vacuum: float) -> Atoms:
    if nz == 1:
        stacked = base.copy()
        stacked.center(vacuum=vacuum / 2.0, axis=2)
        return stacked

    layers = []
    for index in range(nz):
        layer = base.copy()
        layer.positions[:, 2] += index * spacing
        layers.append(layer)

    symbols = []
    positions = []
    for layer in layers:
        symbols.extend(layer.get_chemical_symbols())
        positions.extend(layer.positions)

    positions_array = np.asarray(positions, dtype=float)
    z_min = float(positions_array[:, 2].min())
    positions_array[:, 2] -= z_min
    z_span = float(positions_array[:, 2].max() - positions_array[:, 2].min())

    cell = base.cell.array.copy()
    cell[2] = [0.0, 0.0, z_span + vacuum]
    stacked = Atoms(symbols=symbols, positions=positions_array, cell=cell, pbc=True)
    stacked.center(vacuum=vacuum / 2.0, axis=2)
    return stacked


def build(atoms: Atoms, repeat: tuple[int, int, int], spacing: float, vacuum: float) -> Atoms:
    nx, ny, nz = repeat
    if min(repeat) < 1:
        raise ValueError("--repeat values must all be positive integers")
    atoms = atoms.copy()
    atoms.pbc = (True, True, True)
    xy_repeated = atoms.repeat((nx, ny, 1))
    return stack_z(xy_repeated, nz=nz, spacing=spacing, vacuum=vacuum)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(
            f"Input structure not found: {input_path}. Generate/relax a small cell first.",
            file=sys.stderr,
        )
        return 1

    atoms = read(input_path)
    large = build(
        atoms,
        repeat=tuple(args.repeat),
        spacing=args.stack_spacing,
        vacuum=args.vacuum,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_kwargs = {
        "format": "lammps-data",
        "atom_style": "atomic",
        "specorder": args.specorder,
    }
    if "masses" in inspect.signature(write_lammps_data).parameters:
        write_kwargs["masses"] = True
    write(output, large, **write_kwargs)

    summary = {
        "input": str(input_path),
        "output": str(output),
        "repeat": list(args.repeat),
        "stack_spacing": args.stack_spacing,
        "specorder": args.specorder,
        "natoms": len(large),
        "formula": large.get_chemical_formula(),
        "cell": large.cell.array.round(8).tolist(),
    }
    summary_path = Path(args.summary) if args.summary else output.with_suffix(".summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {output} with {len(large)} atoms")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
