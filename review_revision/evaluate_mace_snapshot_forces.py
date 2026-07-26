#!/usr/bin/env python3
"""Evaluate MACE force errors on completed high-displacement VASP snapshots.

This script turns the already completed MD-snapshot VASP single-point checks
into a real out-of-domain validation test: for each snapshot, it compares the
DFT forces in OUTCAR with forces predicted by one or more MACE models.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from ase.io import read
from mace.calculators import MACECalculator


PAIR_KEYS = (
    ("C", "C"),
    ("C", "Li"),
    ("Li", "Si"),
    ("Li", "Li"),
    ("Si", "Si"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="review_revision/md_snapshot_dft_jobs/md_snapshot_dft_manifest.csv",
        help="CSV written by prepare_md_snapshot_dft_checks.py.",
    )
    parser.add_argument(
        "--model",
        action="append",
        required=True,
        help="MACE .model path. Repeat for multiple models.",
    )
    parser.add_argument(
        "--model-label",
        action="append",
        default=[],
        help="Human-readable model label. Provide one per --model, or omit.",
    )
    parser.add_argument("--output-dir", default="results/review_revision/md_snapshot_mace_eval")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--dtype", default="float64")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    if not keys:
        keys = ["status"]
        rows = [{"status": "empty"}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def safe_label(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "model"


def rmse(values: np.ndarray | list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return float("nan")
    return float(math.sqrt(np.mean(arr * arr)))


def mae(values: np.ndarray | list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return float("nan")
    return float(np.mean(np.abs(arr)))


def min_pair_distances(atoms) -> dict[str, float]:
    symbols = atoms.get_chemical_symbols()
    best = {f"min_{a}_{b}_a": float("nan") for a, b in PAIR_KEYS}
    best_values: dict[tuple[str, str], float] = {}
    for i, sym_i in enumerate(symbols):
        for j in range(i + 1, len(symbols)):
            sym_j = symbols[j]
            pair = tuple(sorted((sym_i, sym_j)))
            if pair not in PAIR_KEYS:
                continue
            distance = float(atoms.get_distance(i, j, mic=True))
            if pair not in best_values or distance < best_values[pair]:
                best_values[pair] = distance
    for pair, distance in best_values.items():
        best[f"min_{pair[0]}_{pair[1]}_a"] = distance
    return best


def load_snapshot(job_dir: Path):
    outcar = job_dir / "OUTCAR"
    if not outcar.exists() or outcar.stat().st_size == 0:
        raise FileNotFoundError(f"missing OUTCAR: {outcar}")
    atoms = read(outcar, index=-1, format="vasp-out")
    dft_energy = float(atoms.get_potential_energy())
    dft_forces = np.asarray(atoms.get_forces(), dtype=float)
    if dft_forces.shape != (len(atoms), 3):
        raise ValueError(f"unexpected force array shape {dft_forces.shape}")
    atoms.calc = None
    return atoms, dft_energy, dft_forces


def evaluate_one_model(
    model_path: Path,
    model_label: str,
    manifest_rows: list[dict[str, str]],
    output_dir: Path,
    device: str,
    dtype: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    if not model_path.exists() or model_path.stat().st_size == 0:
        raise FileNotFoundError(f"missing model: {model_path}")

    calc = MACECalculator(model_paths=str(model_path), device=device, default_dtype=dtype)
    frame_rows: list[dict[str, object]] = []
    failed_rows: list[dict[str, object]] = []

    for manifest in manifest_rows:
        job_dir = Path(manifest["job_dir"])
        case = manifest.get("case", job_dir.name.split("_seed")[0])
        try:
            atoms, dft_energy, dft_forces = load_snapshot(job_dir)
            calc_atoms = atoms.copy()
            calc_atoms.calc = calc
            pred_energy = float(calc_atoms.get_potential_energy())
            pred_forces = np.asarray(calc_atoms.get_forces(), dtype=float)
            force_error = (pred_forces - dft_forces) * 1000.0
            atom_force_norm_error = np.linalg.norm(force_error, axis=1)
            row = {
                "model_label": model_label,
                "model_path": str(model_path),
                "job_dir": str(job_dir),
                "case": case,
                "seed": manifest.get("seed", ""),
                "step": manifest.get("step", ""),
                "time_ps": manifest.get("time_ps", ""),
                "msd_xy_a2": manifest.get("msd_xy_a2", ""),
                "natoms": len(atoms),
                "dft_energy_ev": dft_energy,
                "pred_energy_ev": pred_energy,
                "energy_error_mev_atom": (pred_energy - dft_energy) * 1000.0 / len(atoms),
                "force_rmse_mev_a": rmse(force_error.reshape(-1)),
                "force_mae_mev_a": mae(force_error.reshape(-1)),
                "force_max_component_mev_a": float(np.max(np.abs(force_error))),
                "force_max_atom_norm_mev_a": float(np.max(atom_force_norm_error)),
                "dft_force_rms_mev_a": rmse(dft_forces.reshape(-1) * 1000.0),
                "dft_force_max_atom_norm_mev_a": float(np.max(np.linalg.norm(dft_forces, axis=1)) * 1000.0),
            }
            row.update(min_pair_distances(atoms))
            frame_rows.append(row)
        except Exception as exc:  # noqa: BLE001
            failed_rows.append(
                {
                    "model_label": model_label,
                    "job_dir": str(job_dir),
                    "case": case,
                    "error": str(exc),
                }
            )

    summary_rows = summarize_rows(frame_rows)
    label = safe_label(model_label)
    write_csv(output_dir / f"{label}_snapshot_force_errors.csv", frame_rows)
    write_csv(output_dir / f"{label}_snapshot_force_summary.csv", summary_rows)
    if failed_rows:
        write_csv(output_dir / f"{label}_failed_snapshots.csv", failed_rows)
    return frame_rows, summary_rows, failed_rows


def summarize_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[("ALL", "ALL")].append(row)
        grouped[(str(row["case"]), str(row["case"]))].append(row)

    summaries: list[dict[str, object]] = []
    for (group, case), group_rows in sorted(grouped.items()):
        force = np.asarray([float(row["force_rmse_mev_a"]) for row in group_rows], dtype=float)
        energy = np.asarray([float(row["energy_error_mev_atom"]) for row in group_rows], dtype=float)
        summaries.append(
            {
                "group": group,
                "case": case,
                "n_frames": len(group_rows),
                "energy_rmse_mev_atom": rmse(energy),
                "energy_mean_signed_mev_atom": float(np.mean(energy)),
                "force_rmse_mev_a_frame_mean": float(np.mean(force)),
                "force_rmse_mev_a_frame_median": float(np.median(force)),
                "force_rmse_mev_a_frame_rms": rmse(force),
                "force_rmse_mev_a_frame_max": float(np.max(force)),
                "max_atom_force_error_mev_a": float(
                    np.max([float(row["force_max_atom_norm_mev_a"]) for row in group_rows])
                ),
            }
        )
    return summaries


def write_markdown(output_dir: Path, all_summaries: list[dict[str, object]], all_failed: list[dict[str, object]]) -> None:
    lines = [
        "# MD-Snapshot MACE Force Validation",
        "",
        "This report compares MACE predictions directly against VASP OUTCAR forces",
        "for high-displacement MD snapshots. It is an out-of-domain check; electronic",
        "convergence alone is not treated as validation.",
        "",
        "## Summary",
        "",
        "| Model | Group | n | Energy RMSE (meV/atom) | Force RMSE frame RMS (meV/A) | Max atom force error (meV/A) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in all_summaries:
        lines.append(
            "| {model_label} | {group} | {n_frames} | {energy_rmse_mev_atom:.2f} | "
            "{force_rmse_mev_a_frame_rms:.2f} | {max_atom_force_error_mev_a:.2f} |".format(**row)
        )
    if all_failed:
        lines.extend(["", "## Failed Inputs", ""])
        for row in all_failed:
            lines.append(f"- {row['model_label']} {row['job_dir']}: {row['error']}")
    lines.append("")
    (output_dir / "SNAPSHOT_MACE_FORCE_VALIDATION.md").write_text("\n".join(lines), encoding="utf-8")


def try_plot(output_dir: Path, frame_rows: list[dict[str, object]]) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:  # noqa: BLE001
        return
    if not frame_rows:
        return
    labels = [f"{Path(str(row['job_dir'])).name}\n{row['model_label']}" for row in frame_rows]
    values = [float(row["force_rmse_mev_a"]) for row in frame_rows]
    fig_width = max(8.0, 0.45 * len(labels))
    fig, ax = plt.subplots(figsize=(fig_width, 4.8), constrained_layout=True)
    ax.bar(range(len(labels)), values, color="#4c78a8")
    ax.set_ylabel("Force RMSE (meV/A)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=75, ha="right", fontsize=7)
    ax.set_title("MACE force error on DFT-checked high-displacement snapshots")
    fig.savefig(output_dir / "snapshot_force_rmse.png", dpi=250)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    labels = args.model_label or [Path(model).stem for model in args.model]
    if len(labels) != len(args.model):
        raise ValueError("Provide either no --model-label values or one label per --model")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows = read_csv(Path(args.manifest))
    if not manifest_rows:
        raise ValueError(f"No rows in manifest: {args.manifest}")

    all_frames: list[dict[str, object]] = []
    all_summaries: list[dict[str, object]] = []
    all_failed: list[dict[str, object]] = []
    for model_path, label in zip(args.model, labels, strict=True):
        try:
            frame_rows, summary_rows, failed_rows = evaluate_one_model(
                Path(model_path),
                label,
                manifest_rows,
                output_dir,
                args.device,
                args.dtype,
            )
        except Exception as exc:  # noqa: BLE001
            frame_rows = []
            summary_rows = [
                {
                    "group": "ALL",
                    "case": "ALL",
                    "n_frames": 0,
                    "energy_rmse_mev_atom": float("nan"),
                    "energy_mean_signed_mev_atom": float("nan"),
                    "force_rmse_mev_a_frame_mean": float("nan"),
                    "force_rmse_mev_a_frame_median": float("nan"),
                    "force_rmse_mev_a_frame_rms": float("nan"),
                    "force_rmse_mev_a_frame_max": float("nan"),
                    "max_atom_force_error_mev_a": float("nan"),
                }
            ]
            failed_rows = [
                {
                    "model_label": label,
                    "job_dir": "MODEL_LOAD",
                    "case": "ALL",
                    "error": str(exc),
                }
            ]
        for row in summary_rows:
            row["model_label"] = label
        all_frames.extend(frame_rows)
        all_summaries.extend(summary_rows)
        all_failed.extend(failed_rows)

    write_csv(output_dir / "all_models_snapshot_force_errors.csv", all_frames)
    write_csv(output_dir / "all_models_snapshot_force_summary.csv", all_summaries)
    if all_failed:
        write_csv(output_dir / "all_models_failed_snapshots.csv", all_failed)
    write_markdown(output_dir, all_summaries, all_failed)
    try_plot(output_dir, all_frames)
    print(output_dir / "SNAPSHOT_MACE_FORCE_VALIDATION.md")
    return 1 if all_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
