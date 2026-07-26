#!/usr/bin/env python3
"""Evaluate one or more MACE models on extxyz train/valid/test splits.

This is meant for review response diagnostics: it reports held-out test errors,
family-level errors, and model-vs-DFT parity data for the current DFT labels.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np
from ase.io import read
from mace.calculators import MACECalculator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="append", required=True, help="MACE .model path. Can be given multiple times.")
    parser.add_argument("--model-label", action="append", default=[], help="Label for each model.")
    parser.add_argument("--split", action="append", default=[], help="split_name:path.extxyz. Repeatable.")
    parser.add_argument("--output-dir", default="results/review_revision/mace_eval")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--dtype", default="float64")
    return parser.parse_args()


def parse_splits(values: list[str]) -> dict[str, Path]:
    if not values:
        values = [
            "train:data/mace_datasets/li_mace_train.extxyz",
            "valid:data/mace_datasets/li_mace_valid.extxyz",
            "test:data/mace_datasets/li_mace_test.extxyz",
        ]
    result = {}
    for value in values:
        name, sep, path = value.partition(":")
        if not sep:
            raise ValueError(f"--split must look like name:path.extxyz, got {value}")
        result[name] = Path(path)
    return result


def family_from_atoms(atoms) -> str:
    family = atoms.info.get("family")
    if family:
        return str(family)
    config_type = str(atoms.info.get("config_type", "unknown"))
    for known in ["A_Perfect", "B1_Monovacancy", "B2_Divacancy", "C_StoneWales", "D_SiGraphene"]:
        if config_type.startswith(known) or config_type.startswith(f"SP_{known}"):
            return known
    return config_type.split("_")[0]


def rmse(values: list[float]) -> float:
    if not values:
        return float("nan")
    arr = np.asarray(values, dtype=float)
    return float(math.sqrt(np.mean(arr * arr)))


def read_frames(path: Path):
    frames = read(path, ":")
    if not isinstance(frames, list):
        frames = [frames]
    return frames


def dft_energy_for_atoms(atoms) -> float:
    for key in ("energy", "REF_energy", "dft_energy", "DFT_energy"):
        if key in atoms.info:
            return float(atoms.info[key])
    if atoms.calc is not None and "energy" in getattr(atoms.calc, "results", {}):
        return float(atoms.calc.results["energy"])
    return float(atoms.get_potential_energy())


def dft_forces_for_atoms(atoms) -> np.ndarray:
    for key in ("forces", "REF_forces", "dft_forces", "DFT_forces"):
        if key in atoms.arrays:
            return np.asarray(atoms.arrays[key], dtype=float)
    if atoms.calc is not None and "forces" in getattr(atoms.calc, "results", {}):
        return np.asarray(atoms.calc.results["forces"], dtype=float)
    return np.asarray(atoms.get_forces(), dtype=float)


def evaluate_model(model_path: Path, label: str, splits: dict[str, Path], output_dir: Path, device: str, dtype: str) -> None:
    calc = MACECalculator(model_paths=str(model_path), device=device, default_dtype=dtype)
    parity_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for split, path in splits.items():
        frames = read_frames(path)
        for index, atoms in enumerate(frames):
            dft_e = dft_energy_for_atoms(atoms)
            dft_f = dft_forces_for_atoms(atoms)
            atoms = atoms.copy()
            atoms.calc = None
            atoms.calc = calc
            pred_e = float(atoms.get_potential_energy())
            pred_f = np.asarray(atoms.get_forces(), dtype=float)
            natoms = len(atoms)
            family = family_from_atoms(atoms)
            config_type = str(atoms.info.get("config_type", "unknown"))
            f_err = pred_f - dft_f
            parity_rows.append(
                {
                    "model_label": label,
                    "model_path": str(model_path),
                    "split": split,
                    "frame_index": index,
                    "config_type": config_type,
                    "family": family,
                    "natoms": natoms,
                    "dft_energy_ev": dft_e,
                    "pred_energy_ev": pred_e,
                    "energy_error_mev_atom": (pred_e - dft_e) * 1000.0 / natoms,
                    "force_rmse_mev_a": rmse((f_err.reshape(-1) * 1000.0).tolist()),
                    "dft_force_rms_mev_a": rmse((dft_f.reshape(-1) * 1000.0).tolist()),
                }
            )

    groups: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in parity_rows:
        groups.setdefault((str(row["split"]), str(row["family"])), []).append(row)
        groups.setdefault((str(row["split"]), "ALL"), []).append(row)
    for (split, family), rows in sorted(groups.items()):
        e_errors = [float(row["energy_error_mev_atom"]) for row in rows]
        # Aggregate force RMSE by treating per-frame force RMSE values as frame-level diagnostics.
        f_errors = [float(row["force_rmse_mev_a"]) for row in rows]
        summary_rows.append(
            {
                "model_label": label,
                "split": split,
                "family": family,
                "n_frames": len(rows),
                "energy_rmse_mev_atom": rmse(e_errors),
                "force_rmse_mev_a_frame_mean": float(np.mean(f_errors)),
                "force_rmse_mev_a_frame_rms": rmse(f_errors),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in [("parity", parity_rows), ("summary", summary_rows)]:
        out = output_dir / f"{label}_{name}.csv"
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(out)


def main() -> int:
    args = parse_args()
    splits = parse_splits(args.split)
    labels = args.model_label or [Path(model).stem for model in args.model]
    if len(labels) != len(args.model):
        raise ValueError("Provide either no --model-label values or one label per --model")
    for split, path in splits.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing split {split}: {path}")
    for model, label in zip(args.model, labels, strict=True):
        evaluate_model(Path(model), label, splits, Path(args.output_dir), args.device, args.dtype)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
