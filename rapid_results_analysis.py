#!/usr/bin/env python3
"""Generate two-day-rush analysis tables and figures from existing labels.

This script is intentionally useful even when MACE cannot be imported on a CPU
node: the DFT/SP energy landscape and training-log figures are produced first.
If a MACE model is supplied and imports cleanly, parity predictions are added.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

import numpy as np
from ase.io import read

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # noqa: BLE001
    plt = None


FAMILIES = (
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", default="data/mace_datasets")
    parser.add_argument("--sp-root", default="dft_sp_outputs")
    parser.add_argument("--training-log", default="local_3060ti_finetune_pack/logs/local_li_mace_v1/li_mace_v1_3060ti_run-20260427.log")
    parser.add_argument("--output-dir", default="results/two_day_rush")
    parser.add_argument("--model", default="local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1/li_mace_v1_3060ti_stagetwo.model")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--dtype", default="float32")
    parser.add_argument("--max-parity-frames", type=int, default=500)
    parser.add_argument("--skip-model-predictions", action="store_true")
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def family_from_config(config_type: str) -> str:
    stripped = re.sub(r"^SP_", "", config_type)
    for family in FAMILIES:
        if stripped == family or stripped.startswith(f"{family}_"):
            return family
    return stripped.split("_path")[0]


def frame_energy(atoms) -> float:
    if "energy" in atoms.info:
        return float(atoms.info["energy"])
    return float(atoms.get_potential_energy())


def frame_forces(atoms) -> np.ndarray:
    if "forces" in atoms.arrays:
        return np.asarray(atoms.arrays["forces"], dtype=float)
    return np.asarray(atoms.get_forces(), dtype=float)


def summarize_dataset(dataset_dir: Path, output_dir: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    split_summary: dict[str, object] = {}
    for split in ("train", "valid", "test", "all"):
        path = dataset_dir / f"li_mace_{split}.extxyz"
        if not path.exists() or path.stat().st_size == 0:
            split_summary[split] = {"frames": 0, "path": str(path)}
            continue
        frames = read(path, ":")
        if not isinstance(frames, list):
            frames = [frames]
        energies = []
        max_forces = []
        families = Counter()
        configs = Counter()
        natoms = Counter()
        for index, atoms in enumerate(frames):
            config_type = str(atoms.info.get("config_type", "Default"))
            family = str(atoms.info.get("family") or family_from_config(config_type))
            energy = frame_energy(atoms)
            forces = frame_forces(atoms)
            max_force = float(np.max(np.linalg.norm(forces, axis=1)))
            energies.append(energy)
            max_forces.append(max_force)
            families[family] += 1
            configs[config_type] += 1
            natoms[len(atoms)] += 1
            rows.append(
                {
                    "split": split,
                    "frame_index": index,
                    "family": family,
                    "config_type": config_type,
                    "natoms": len(atoms),
                    "energy_ev": energy,
                    "max_force_ev_a": max_force,
                    "formula": atoms.get_chemical_formula(),
                }
            )
        split_summary[split] = {
            "path": str(path),
            "frames": len(frames),
            "families": dict(families),
            "natoms": dict(natoms),
            "config_types": dict(configs),
            "energy_min_ev": min(energies),
            "energy_max_ev": max(energies),
            "max_force_max_ev_a": max(max_forces),
        }

    write_csv(output_dir / "dataset_frames.csv", rows)
    (output_dir / "dataset_summary.json").write_text(
        json.dumps(split_summary, indent=2),
        encoding="utf-8",
    )

    if plt and rows:
        all_rows = [row for row in rows if row["split"] == "all"]
        counts = Counter(str(row["family"]) for row in all_rows)
        fig, ax = plt.subplots(figsize=(7.0, 3.8))
        ax.bar(list(counts), [counts[key] for key in counts], color="#5577aa")
        ax.set_ylabel("Frames")
        ax.set_title("MACE dataset composition")
        ax.tick_params(axis="x", rotation=25)
        fig.tight_layout()
        fig.savefig(output_dir / "dataset_family_counts.png", dpi=220)
        plt.close(fig)
    return split_summary


def parse_sp_name(name: str) -> dict[str, object]:
    stripped = re.sub(r"^SP_", "", name)
    family = None
    suffix = stripped
    for candidate in FAMILIES:
        if stripped.startswith(f"{candidate}_"):
            family = candidate
            suffix = stripped[len(candidate) + 1 :]
            break
    if family is None:
        family = stripped.split("_", 1)[0]
        suffix = stripped.split("_", 1)[1] if "_" in stripped else ""

    record: dict[str, object] = {
        "case": name,
        "family": family,
        "label": suffix,
        "kind": "site",
        "path_id": "",
        "path_start": "",
        "path_end": "",
        "image_index": "",
    }
    match = re.match(r"(?P<path_id>path\d+)_(?P<start>.+)_to_(?P<end>.+)_img(?P<img>\d+)$", suffix)
    if match:
        record.update(
            {
                "kind": "path",
                "path_id": match.group("path_id"),
                "path_start": match.group("start"),
                "path_end": match.group("end"),
                "image_index": int(match.group("img")),
            }
        )
    return record


def collect_sp_energies(sp_root: Path, output_dir: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for job_dir in sorted(path for path in sp_root.iterdir() if path.is_dir()) if sp_root.exists() else []:
        outcar = job_dir / "OUTCAR"
        record = parse_sp_name(job_dir.name)
        record["path"] = str(job_dir)
        if not outcar.exists() or outcar.stat().st_size == 0:
            failures.append({**record, "error": "missing OUTCAR"})
            continue
        try:
            atoms = read(outcar, index=-1, format="vasp-out")
            forces = np.asarray(atoms.get_forces(), dtype=float)
            record.update(
                {
                    "natoms": len(atoms),
                    "formula": atoms.get_chemical_formula(),
                    "energy_ev": float(atoms.get_potential_energy()),
                    "max_force_ev_a": float(np.max(np.linalg.norm(forces, axis=1))),
                }
            )
            rows.append(record)
        except Exception as exc:  # noqa: BLE001
            failures.append({**record, "error": str(exc)})

    family_min: dict[str, float] = {}
    site_family_min: dict[str, float] = {}
    for row in rows:
        family = str(row["family"])
        energy = float(row["energy_ev"])
        family_min[family] = min(family_min.get(family, energy), energy)
        if row["kind"] == "site":
            site_family_min[family] = min(site_family_min.get(family, energy), energy)
    for row in rows:
        family = str(row["family"])
        row["rel_to_family_min_ev"] = float(row["energy_ev"]) - family_min[family]
        row["rel_to_site_min_ev"] = float(row["energy_ev"]) - site_family_min.get(family, family_min[family])

    write_csv(output_dir / "sp_energies.csv", rows)
    write_csv(output_dir / "sp_parse_failures.csv", failures)
    return rows, failures


def summarize_sites_and_paths(sp_rows: list[dict[str, object]], output_dir: Path) -> list[dict[str, object]]:
    site_rows = [row for row in sp_rows if row["kind"] == "site"]
    site_rows = sorted(site_rows, key=lambda row: (str(row["family"]), float(row["rel_to_site_min_ev"])))
    write_csv(output_dir / "site_energy_rankings.csv", site_rows)

    path_rows_by_key: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    site_energy: dict[tuple[str, str], float] = {}
    for row in sp_rows:
        family = str(row["family"])
        if row["kind"] == "site":
            site_energy[(family, str(row["label"]))] = float(row["energy_ev"])
        else:
            path_rows_by_key[(family, str(row["path_id"]))].append(row)

    profile_rows: list[dict[str, object]] = []
    barrier_rows: list[dict[str, object]] = []
    for (family, path_id), rows in sorted(path_rows_by_key.items()):
        rows = sorted(rows, key=lambda row: int(row["image_index"]))
        start = str(rows[0]["path_start"])
        end = str(rows[0]["path_end"])
        energies: list[tuple[int, str, float, str]] = []
        if (family, start) in site_energy:
            energies.append((0, start, site_energy[(family, start)], "endpoint"))
        for index, row in enumerate(rows, start=1):
            energies.append((index, f"img{int(row['image_index']):02d}", float(row["energy_ev"]), "image"))
        if (family, end) in site_energy:
            energies.append((len(energies), end, site_energy[(family, end)], "endpoint"))

        if not energies:
            continue
        e0 = energies[0][2]
        emin = min(value for _, _, value, _ in energies)
        emax = max(value for _, _, value, _ in energies)
        for reaction_coord, label, energy, point_kind in energies:
            profile_rows.append(
                {
                    "family": family,
                    "path_id": path_id,
                    "path_start": start,
                    "path_end": end,
                    "reaction_index": reaction_coord,
                    "point_label": label,
                    "point_kind": point_kind,
                    "energy_ev": energy,
                    "rel_to_start_ev": energy - e0,
                    "rel_to_path_min_ev": energy - emin,
                }
            )
        barrier_rows.append(
            {
                "family": family,
                "path_id": path_id,
                "path_start": start,
                "path_end": end,
                "n_points": len(energies),
                "start_energy_ev": e0,
                "end_energy_ev": energies[-1][2],
                "barrier_from_start_ev": emax - e0,
                "barrier_from_path_min_ev": emax - emin,
                "delta_e_end_minus_start_ev": energies[-1][2] - e0,
            }
        )

    write_csv(output_dir / "path_profiles.csv", profile_rows)
    write_csv(output_dir / "path_barriers.csv", barrier_rows)

    if plt and site_rows:
        families = [family for family in FAMILIES if any(row["family"] == family for row in site_rows)]
        fig, axes = plt.subplots(len(families), 1, figsize=(8.0, max(3.0, 2.2 * len(families))), squeeze=False)
        for ax, family in zip(axes[:, 0], families):
            subset = [row for row in site_rows if row["family"] == family]
            labels = [str(row["label"]) for row in subset]
            values = [float(row["rel_to_site_min_ev"]) for row in subset]
            ax.bar(labels, values, color="#5f8f6f")
            ax.set_ylabel("eV")
            ax.set_title(f"{family}: Li site energies relative to site minimum")
            ax.tick_params(axis="x", rotation=25, labelsize=8)
        fig.tight_layout()
        fig.savefig(output_dir / "site_energy_rankings.png", dpi=220)
        plt.close(fig)

    if plt and profile_rows:
        fig, ax = plt.subplots(figsize=(8.2, 4.8))
        for (family, path_id), rows in sorted(
            defaultdict(list, {
                key: [row for row in profile_rows if (row["family"], row["path_id"]) == key]
                for key in sorted({(row["family"], row["path_id"]) for row in profile_rows})
            }).items()
        ):
            rows = sorted(rows, key=lambda row: int(row["reaction_index"]))
            label = f"{family} {path_id}"
            ax.plot(
                [int(row["reaction_index"]) for row in rows],
                [float(row["rel_to_path_min_ev"]) for row in rows],
                marker="o",
                linewidth=1.3,
                markersize=3.5,
                label=label,
            )
        ax.set_xlabel("Path point index")
        ax.set_ylabel("Energy relative to path minimum (eV)")
        ax.set_title("DFT Li diffusion path profiles")
        ax.legend(fontsize=6.5, ncol=2)
        fig.tight_layout()
        fig.savefig(output_dir / "path_profiles.png", dpi=220)
        plt.close(fig)
    return barrier_rows


def parse_training_log(log_path: Path, output_dir: Path) -> list[dict[str, object]]:
    if not log_path.exists():
        return []
    rows: list[dict[str, object]] = []
    pattern = re.compile(
        r"Epoch\s+(?P<epoch>\d+):.*?loss=(?P<loss>[0-9.eE+-]+),\s+"
        r"RMSE_E_per_atom=\s*(?P<e>[0-9.]+)\s+meV,\s+"
        r"RMSE_F=\s*(?P<f>[0-9.]+)\s+meV"
    )
    for line in log_path.read_text(errors="replace").splitlines():
        match = pattern.search(line)
        if not match:
            continue
        rows.append(
            {
                "epoch": int(match.group("epoch")),
                "loss": float(match.group("loss")),
                "rmse_e_mev_atom": float(match.group("e")),
                "rmse_f_mev_a": float(match.group("f")),
            }
        )
    write_csv(output_dir / "training_curve.csv", rows)
    if plt and rows:
        fig, ax1 = plt.subplots(figsize=(7.2, 4.0))
        epochs = [int(row["epoch"]) for row in rows]
        ax1.plot(epochs, [float(row["rmse_e_mev_atom"]) for row in rows], color="#345995", label="Energy RMSE")
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("Energy RMSE (meV/atom)", color="#345995")
        ax1.tick_params(axis="y", labelcolor="#345995")
        ax2 = ax1.twinx()
        ax2.plot(epochs, [float(row["rmse_f_mev_a"]) for row in rows], color="#d35400", label="Force RMSE")
        ax2.set_ylabel("Force RMSE (meV/A)", color="#d35400")
        ax2.tick_params(axis="y", labelcolor="#d35400")
        ax1.set_title("MACE fine-tuning training curve")
        fig.tight_layout()
        fig.savefig(output_dir / "training_curve.png", dpi=220)
        plt.close(fig)
    return rows


def parse_error_tables(log_path: Path, output_dir: Path) -> list[dict[str, object]]:
    """Parse MACE ASCII error tables from the training log."""
    if not log_path.exists():
        return []
    rows: list[dict[str, object]] = []
    current_section = ""
    table_index: dict[str, int] = defaultdict(int)
    line_pattern = re.compile(
        r"^\|\s*(?P<config>[^|]+?)\s*\|\s*"
        r"(?P<energy>[0-9.]+)\s*\|\s*"
        r"(?P<force>[0-9.]+)\s*\|\s*"
        r"(?P<rel_force>[0-9.]+)\s*\|"
    )
    for line in log_path.read_text(errors="replace").splitlines():
        if "Error-table on TRAIN and VALID" in line:
            current_section = "train_valid"
            table_index[current_section] += 1
            continue
        if "Error-table on TEST" in line:
            current_section = "test"
            table_index[current_section] += 1
            continue
        match = line_pattern.match(line)
        if not match or not current_section:
            continue
        config = match.group("config").strip()
        if config == "config_type":
            continue
        rows.append(
            {
                "section": current_section,
                "table_index": table_index[current_section],
                "config_type": config,
                "rmse_e_mev_atom": float(match.group("energy")),
                "rmse_f_mev_a": float(match.group("force")),
                "relative_f_rmse_percent": float(match.group("rel_force")),
            }
        )
    write_csv(output_dir / "mace_error_tables_all.csv", rows)
    if rows:
        last_index = {
            section: max(int(row["table_index"]) for row in rows if row["section"] == section)
            for section in sorted({str(row["section"]) for row in rows})
        }
        final_rows = [
            row for row in rows
            if int(row["table_index"]) == last_index[str(row["section"])]
        ]
        write_csv(output_dir / "mace_error_table_final.csv", final_rows)
    return rows


def metrics(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    return {
        "mae": float(np.mean(np.abs(values))),
        "rmse": float(math.sqrt(float(np.mean(values**2)))),
        "mean": float(np.mean(values)),
        "max_abs": float(np.max(np.abs(values))),
    }


def load_mace_calculator(model: Path, device: str, dtype: str):
    from mace.calculators import MACECalculator

    try:
        return MACECalculator(model_paths=str(model), device=device, default_dtype=dtype)
    except TypeError:
        return MACECalculator(model_paths=[str(model)], device=device, default_dtype=dtype)


def run_mace_parity(args: argparse.Namespace, output_dir: Path) -> dict[str, object]:
    if args.skip_model_predictions:
        return {"skipped": True, "reason": "requested with --skip-model-predictions"}
    model = Path(args.model)
    if not model.exists():
        return {"skipped": True, "reason": f"model not found: {model}"}
    try:
        calc = load_mace_calculator(model, args.device, args.dtype)
    except Exception as exc:  # noqa: BLE001
        return {"skipped": True, "reason": f"failed to load MACE calculator: {exc}"}

    rows: list[dict[str, object]] = []
    force_dft: list[float] = []
    force_mace: list[float] = []
    energy_errors: list[float] = []
    force_errors: list[float] = []
    for split in ("train", "valid", "test"):
        path = Path(args.dataset_dir) / f"li_mace_{split}.extxyz"
        if not path.exists() or path.stat().st_size == 0:
            continue
        frames = read(path, ":")
        if not isinstance(frames, list):
            frames = [frames]
        for frame_index, atoms in enumerate(frames[: args.max_parity_frames]):
            dft_energy = frame_energy(atoms)
            dft_forces = frame_forces(atoms)
            pred = atoms.copy()
            pred.calc = calc
            mace_energy = float(pred.get_potential_energy())
            mace_forces = np.asarray(pred.get_forces(), dtype=float)
            e_err_pa = (mace_energy - dft_energy) / len(atoms)
            f_err = (mace_forces - dft_forces).reshape(-1)
            rows.append(
                {
                    "split": split,
                    "frame_index": frame_index,
                    "family": str(atoms.info.get("family") or family_from_config(str(atoms.info.get("config_type", "Default")))),
                    "config_type": str(atoms.info.get("config_type", "Default")),
                    "natoms": len(atoms),
                    "dft_energy_ev": dft_energy,
                    "mace_energy_ev": mace_energy,
                    "energy_error_ev_atom": e_err_pa,
                    "force_rmse_ev_a": math.sqrt(float(np.mean(f_err**2))),
                }
            )
            energy_errors.append(e_err_pa)
            force_errors.extend(f_err.tolist())
            force_dft.extend(dft_forces.reshape(-1).tolist())
            force_mace.extend(mace_forces.reshape(-1).tolist())

    write_csv(output_dir / "mace_parity_frames.csv", rows)
    summary = {
        "model": str(model),
        "device": args.device,
        "dtype": args.dtype,
        "n_frames": len(rows),
        "energy_ev_atom": metrics(np.asarray(energy_errors)) if energy_errors else {},
        "force_ev_a": metrics(np.asarray(force_errors)) if force_errors else {},
    }
    (output_dir / "mace_parity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if plt and rows:
        fig, ax = plt.subplots(figsize=(4.8, 4.8))
        x = [float(row["dft_energy_ev"]) / int(row["natoms"]) for row in rows]
        y = [float(row["mace_energy_ev"]) / int(row["natoms"]) for row in rows]
        ax.scatter(x, y, s=14, alpha=0.7)
        lo, hi = min(x + y), max(x + y)
        ax.plot([lo, hi], [lo, hi], color="black", linewidth=1)
        ax.set_xlabel("DFT energy (eV/atom)")
        ax.set_ylabel("MACE energy (eV/atom)")
        ax.set_title("Energy parity")
        fig.tight_layout()
        fig.savefig(output_dir / "mace_energy_parity.png", dpi=220)
        plt.close(fig)

        sample_step = max(1, len(force_dft) // 5000)
        fig, ax = plt.subplots(figsize=(4.8, 4.8))
        ax.scatter(force_dft[::sample_step], force_mace[::sample_step], s=4, alpha=0.25)
        lo, hi = min(force_dft + force_mace), max(force_dft + force_mace)
        ax.plot([lo, hi], [lo, hi], color="black", linewidth=1)
        ax.set_xlabel("DFT force component (eV/A)")
        ax.set_ylabel("MACE force component (eV/A)")
        ax.set_title("Force parity")
        fig.tight_layout()
        fig.savefig(output_dir / "mace_force_parity.png", dpi=220)
        plt.close(fig)
    return summary


def write_markdown_summary(
    output_dir: Path,
    dataset_summary: dict[str, object],
    sp_rows: list[dict[str, object]],
    failures: list[dict[str, object]],
    barriers: list[dict[str, object]],
    train_rows: list[dict[str, object]],
    error_table_rows: list[dict[str, object]],
    parity_summary: dict[str, object],
) -> None:
    lines = [
        "# Two-Day Rush Results",
        "",
        "## Dataset",
        f"- Total frames: {dataset_summary.get('all', {}).get('frames', 'n/a')}",
        f"- Train/valid/test: {dataset_summary.get('train', {}).get('frames', 'n/a')} / {dataset_summary.get('valid', {}).get('frames', 'n/a')} / {dataset_summary.get('test', {}).get('frames', 'n/a')}",
        "",
        "## DFT Single-Point Labels",
        f"- Parsed SP jobs: {len(sp_rows)}",
        f"- Parse failures: {len(failures)}",
        "",
        "## Lowest-Energy Li Sites",
    ]
    site_rows = [row for row in sp_rows if row["kind"] == "site"]
    for family in FAMILIES:
        subset = sorted([row for row in site_rows if row["family"] == family], key=lambda row: float(row["rel_to_site_min_ev"]))
        if subset:
            best = subset[0]
            lines.append(f"- {family}: {best['label']} ({float(best['rel_to_site_min_ev']):.3f} eV)")
    lines.extend(["", "## Diffusion Barrier Estimates"])
    for row in barriers:
        lines.append(
            f"- {row['family']} {row['path_id']} {row['path_start']} -> {row['path_end']}: "
            f"{float(row['barrier_from_path_min_ev']):.3f} eV from path minimum; "
            f"{float(row['barrier_from_start_ev']):.3f} eV from start"
        )
    if train_rows:
        last = train_rows[-1]
        lines.extend(
            [
                "",
                "## Training Curve",
                f"- Last logged epoch: {last['epoch']}",
                f"- Last logged energy RMSE: {float(last['rmse_e_mev_atom']):.2f} meV/atom",
                f"- Last logged force RMSE: {float(last['rmse_f_mev_a']):.2f} meV/A",
            ]
        )
    if error_table_rows:
        final_train_valid = [
            row for row in error_table_rows
            if row["section"] == "train_valid"
            and int(row["table_index"]) == max(int(item["table_index"]) for item in error_table_rows if item["section"] == "train_valid")
        ]
        lines.extend(["", "## Final MACE Error Table"])
        for row in final_train_valid:
            lines.append(
                f"- {row['config_type']}: {float(row['rmse_e_mev_atom']):.1f} meV/atom, "
                f"{float(row['rmse_f_mev_a']):.1f} meV/A"
            )
    if parity_summary:
        lines.extend(["", "## MACE Parity"])
        if parity_summary.get("skipped"):
            lines.append(f"- Skipped: {parity_summary.get('reason')}")
        else:
            e = parity_summary.get("energy_ev_atom", {})
            f = parity_summary.get("force_ev_a", {})
            lines.append(f"- Energy MAE: {1000.0 * float(e.get('mae', 0.0)):.2f} meV/atom")
            lines.append(f"- Force MAE: {1000.0 * float(f.get('mae', 0.0)):.2f} meV/A")
    lines.extend(
        [
            "",
            "## Key Files",
            "- `dataset_summary.json`, `dataset_frames.csv`",
            "- `site_energy_rankings.csv`, `path_barriers.csv`, `path_profiles.csv`",
            "- `mace_error_table_final.csv`, `training_curve.csv`",
            "- `site_energy_rankings.png`, `path_profiles.png`, `training_curve.png`",
            "- Optional: `mace_parity_summary.json`, `mace_energy_parity.png`, `mace_force_parity.png`",
        ]
    )
    (output_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_summary = summarize_dataset(Path(args.dataset_dir), output_dir)
    sp_rows, failures = collect_sp_energies(Path(args.sp_root), output_dir)
    barriers = summarize_sites_and_paths(sp_rows, output_dir)
    train_rows = parse_training_log(Path(args.training_log), output_dir)
    error_table_rows = parse_error_tables(Path(args.training_log), output_dir)
    parity_summary = run_mace_parity(args, output_dir)
    write_markdown_summary(output_dir, dataset_summary, sp_rows, failures, barriers, train_rows, error_table_rows, parity_summary)
    print(f"Wrote rapid analysis outputs to {output_dir}")
    if failures:
        print(f"Warning: {len(failures)} SP jobs failed to parse; see sp_parse_failures.csv", file=sys.stderr)
    if parity_summary.get("skipped"):
        print(f"MACE parity skipped: {parity_summary.get('reason')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
