#!/usr/bin/env python3
"""Collect VASP OUTCAR frames into a MACE-compatible extxyz file."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
from ase.io import read, write


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse VASP OUTCAR files and write one training extxyz file."
    )
    parser.add_argument("--input-glob", default="dft_outputs/**/OUTCAR")
    parser.add_argument("--output", default="data/train_data.extxyz")
    parser.add_argument(
        "--all-steps",
        action="store_true",
        help="Use all ionic steps instead of only the final frame from each OUTCAR.",
    )
    parser.add_argument(
        "--include-stress",
        action="store_true",
        help="Include stress if ASE can read it from the OUTCAR.",
    )
    parser.add_argument("--report", default=None, help="Optional JSON report path.")
    return parser.parse_args()


def normalize_frame(atoms, source: Path, frame_index: int, include_stress: bool):
    try:
        energy = float(atoms.get_potential_energy())
        forces = np.asarray(atoms.get_forces(), dtype=float)
        stress = None
        if include_stress:
            try:
                stress = np.asarray(atoms.get_stress(voigt=False), dtype=float)
            except Exception:
                stress = np.zeros((3, 3), dtype=float)
    except Exception as exc:  # noqa: BLE001 - expose source file context.
        raise RuntimeError(f"missing energy or forces: {exc}") from exc

    # ASE versions differ on whether Atoms.copy() preserves attached calculators.
    # Extract calculator-backed quantities before copying and detaching calc.
    atoms = atoms.copy()
    atoms.info["energy"] = energy
    atoms.info["config_type"] = source.parent.name or "Default"
    atoms.info["source_outcar"] = str(source)
    atoms.info["source_frame"] = frame_index
    atoms.arrays["forces"] = forces

    if include_stress:
        atoms.info["stress"] = stress

    atoms.calc = None
    return atoms


def read_outcar(path: Path, all_steps: bool, include_stress: bool):
    index = ":" if all_steps else "-1"
    frames = read(path, index=index, format="vasp-out")
    if not isinstance(frames, list):
        frames = [frames]
    return [
        normalize_frame(frame, path, index_in_file, include_stress)
        for index_in_file, frame in enumerate(frames)
    ]


def main() -> int:
    args = parse_args()
    paths = [Path(path) for path in sorted(glob.glob(args.input_glob, recursive=True))]
    if not paths:
        print(f"No OUTCAR files matched {args.input_glob!r}", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path = Path(args.report) if args.report else output.with_suffix(".report.json")

    frames = []
    report = {"read": [], "failed": []}
    for path in paths:
        try:
            new_frames = read_outcar(path, args.all_steps, args.include_stress)
            frames.extend(new_frames)
            report["read"].append({"file": str(path), "frames": len(new_frames)})
        except Exception as exc:  # noqa: BLE001 - continue parsing other OUTCARs.
            report["failed"].append({"file": str(path), "error": str(exc)})

    if not frames:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"No frames were parsed. See {report_path}", file=sys.stderr)
        return 1

    write(output, frames, format="extxyz")
    report["output"] = str(output)
    report["n_frames"] = len(frames)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {len(frames)} frames to {output}")
    print(f"Wrote report to {report_path}")
    if report["failed"]:
        print(f"Skipped {len(report['failed'])} OUTCAR files with parse errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
