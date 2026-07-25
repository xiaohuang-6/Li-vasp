#!/usr/bin/env python3
"""Analyze local reviewer GPU outputs after they are copied back to the cluster.

The analysis is intentionally conservative: it reports 100 ps MD stability and
short-window MSD slopes as reviewer-response diagnostics, not final converged
diffusion coefficients.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # noqa: BLE001
    plt = None


THERMO_RE = re.compile(
    r"^\s*(?P<step>\d+)\s+(?P<time>[-+0-9.eE]+)\s+(?P<temp>[-+0-9.eE]+)\s+"
    r"(?P<pe>[-+0-9.eE]+)\s+(?P<ke>[-+0-9.eE]+)\s+(?P<etotal>[-+0-9.eE]+)\s+"
    r"(?P<press>[-+0-9.eE]+)\s+(?P<vol>[-+0-9.eE]+)\s+"
    r"(?P<msd_x>[-+0-9.eE]+)\s+(?P<msd_y>[-+0-9.eE]+)\s+"
    r"(?P<msd_z>[-+0-9.eE]+)\s+(?P<msd_total>[-+0-9.eE]+)"
)
RUN_RE = re.compile(r"(?P<case>.+)_400K_seed(?P<seed>\d+)_(?P<steps>\d+)steps\.log$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        required=True,
        help="Extracted local_5080_reviewer_gpu_pack directory containing results/review_revision.",
    )
    parser.add_argument("--output-dir", default="results/review_revision/gpu_analysis")
    return parser.parse_args()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys or ["status"])
        writer.writeheader()
        writer.writerows(rows)


def parse_mace_eval(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    eval_dir = root / "results/review_revision/mace_eval"
    rows: list[dict[str, object]] = []
    for path in sorted(eval_dir.glob("*_summary.csv")):
        for row in read_csv_rows(path):
            rows.append(
                {
                    "model_label": row["model_label"],
                    "split": row["split"],
                    "family": row["family"],
                    "n_frames": int(row["n_frames"]),
                    "energy_rmse_mev_atom": float(row["energy_rmse_mev_atom"]),
                    "force_rmse_mev_a_frame_mean": float(row["force_rmse_mev_a_frame_mean"]),
                    "force_rmse_mev_a_frame_rms": float(row["force_rmse_mev_a_frame_rms"]),
                }
            )

    by_key: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        by_key[(str(row["split"]), str(row["family"]), str(row["model_label"]))] = row

    improvements: list[dict[str, object]] = []
    labels = {str(row["model_label"]) for row in rows}
    if {"foundation_mpa0", "finetuned_3060ti"}.issubset(labels):
        keys = sorted({(str(row["split"]), str(row["family"])) for row in rows})
        for split, family in keys:
            ft = by_key.get((split, family, "finetuned_3060ti"))
            base = by_key.get((split, family, "foundation_mpa0"))
            if not ft or not base:
                continue
            base_force = float(base["force_rmse_mev_a_frame_rms"])
            ft_force = float(ft["force_rmse_mev_a_frame_rms"])
            base_energy = float(base["energy_rmse_mev_atom"])
            ft_energy = float(ft["energy_rmse_mev_atom"])
            improvements.append(
                {
                    "split": split,
                    "family": family,
                    "foundation_energy_rmse_mev_atom": base_energy,
                    "finetuned_energy_rmse_mev_atom": ft_energy,
                    "energy_rmse_delta_mev_atom": ft_energy - base_energy,
                    "foundation_force_rmse_mev_a": base_force,
                    "finetuned_force_rmse_mev_a": ft_force,
                    "force_rmse_reduction_pct": 100.0 * (base_force - ft_force) / base_force if base_force else math.nan,
                }
            )
    return rows, improvements


def parse_committee(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    models_dir = root / "models/review_revision"
    logs_dir = root / "logs"
    for model in sorted(models_dir.glob("li_mace_review_seed*.model")):
        if "_compiled" in model.name or "_stagetwo" in model.name:
            continue
        seed_match = re.search(r"seed(\d+)", model.name)
        seed = seed_match.group(1) if seed_match else ""
        log = logs_dir / f"review_committee_seed{seed}.log"
        text = log.read_text(errors="replace") if log.exists() else ""
        done = "Done" in text and "Trained model:" in text
        train_valid = re.findall(r"\|\s*(train_Default|valid_Default)\s*\|\s*([-+0-9.]+)\s*\|\s*([-+0-9.]+)", text)
        parsed = {name: (float(e), float(f)) for name, e, f in train_valid[-2:]}
        rows.append(
            {
                "seed": seed,
                "model": str(model),
                "stagetwo_model_exists": (models_dir / f"li_mace_review_seed{seed}_stagetwo.model").exists(),
                "compiled_model_exists": (models_dir / f"li_mace_review_seed{seed}_compiled.model").exists(),
                "log": str(log) if log.exists() else "",
                "completed": done,
                "train_energy_rmse_mev_atom": parsed.get("train_Default", (math.nan, math.nan))[0],
                "train_force_rmse_mev_a": parsed.get("train_Default", (math.nan, math.nan))[1],
                "valid_energy_rmse_mev_atom": parsed.get("valid_Default", (math.nan, math.nan))[0],
                "valid_force_rmse_mev_a": parsed.get("valid_Default", (math.nan, math.nan))[1],
            }
        )
    return rows


def parse_log_segments(path: Path) -> list[list[dict[str, float]]]:
    segments: list[list[dict[str, float]]] = []
    current: list[dict[str, float]] = []
    for line in path.read_text(errors="replace").splitlines():
        if line.strip().startswith("Step") and "c_li_msd[4]" in line:
            if current:
                segments.append(current)
            current = []
            continue
        match = THERMO_RE.match(line)
        if match:
            current.append({key: float(value) for key, value in match.groupdict().items()})
    if current:
        segments.append(current)
    return segments


def fit_slope(times: np.ndarray, values: np.ndarray, start_fraction: float = 0.2) -> float:
    if len(times) < 3:
        return math.nan
    threshold = times.min() + start_fraction * (times.max() - times.min())
    mask = times >= threshold
    if mask.sum() < 3:
        return math.nan
    slope, _intercept = np.polyfit(times[mask], values[mask], deg=1)
    return float(slope)


def parse_md(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    traces: list[dict[str, object]] = []
    for log in sorted((root / "review_revision/md_logs").glob("*100000steps.log")):
        match = RUN_RE.match(log.name)
        if not match:
            continue
        text = log.read_text(errors="replace")
        segments = parse_log_segments(log)
        production = max(segments, key=len) if segments else []
        if not production:
            continue
        first = production[0]
        last = production[-1]
        arr = {key: np.array([row[key] for row in production], dtype=float) for key in production[0]}
        slope_total = fit_slope(arr["time"], arr["msd_total"])
        slope_xy = fit_slope(arr["time"], arr["msd_x"] + arr["msd_y"])
        # 1 A^2/ps = 1e-4 cm^2/s. Use 3D and 2D Einstein relations.
        d3_cm2_s = slope_total * 1.0e-4 / 6.0 if not math.isnan(slope_total) else math.nan
        dxy_cm2_s = slope_xy * 1.0e-4 / 4.0 if not math.isnan(slope_xy) else math.nan
        case = match.group("case")
        seed = match.group("seed")
        rows.append(
            {
                "case": case,
                "seed": seed,
                "steps": int(match.group("steps")),
                "n_thermo_rows": len(production),
                "completed_100ps": int(last["step"]) >= 100000 and "Total wall time:" in text,
                "lost_atoms_or_error": bool(re.search(r"Lost atoms|ERROR|nan|NaN", text)),
                "dangerous_builds": int(re.findall(r"Dangerous builds =\s+(\d+)", text)[-1]) if re.findall(r"Dangerous builds =\s+(\d+)", text) else math.nan,
                "mean_temp_k": float(np.mean(arr["temp"])),
                "std_temp_k": float(np.std(arr["temp"])),
                "energy_drift_ev": float(last["etotal"] - first["etotal"]),
                "final_msd_total_a2": float(last["msd_total"]),
                "final_msd_xy_a2": float(last["msd_x"] + last["msd_y"]),
                "final_msd_z_a2": float(last["msd_z"]),
                "slope_total_a2_ps": slope_total,
                "slope_xy_a2_ps": slope_xy,
                "diffusion_3d_cm2_s_short": d3_cm2_s,
                "diffusion_xy_cm2_s_short": dxy_cm2_s,
                "log": str(log),
            }
        )
        for idx in np.linspace(0, len(production) - 1, min(101, len(production)), dtype=int):
            traces.append(
                {
                    "case": case,
                    "seed": seed,
                    "time_ps": production[idx]["time"],
                    "msd_total_a2": production[idx]["msd_total"],
                    "msd_xy_a2": production[idx]["msd_x"] + production[idx]["msd_y"],
                    "msd_z_a2": production[idx]["msd_z"],
                }
            )
    return rows, traces


def aggregate_md(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["case"])].append(row)
    out: list[dict[str, object]] = []
    for case, items in sorted(grouped.items()):
        dxy = np.array([float(row["diffusion_xy_cm2_s_short"]) for row in items], dtype=float)
        msd = np.array([float(row["final_msd_xy_a2"]) for row in items], dtype=float)
        out.append(
            {
                "case": case,
                "n_seeds": len(items),
                "all_completed": all(bool(row["completed_100ps"]) for row in items),
                "any_lost_atoms_or_error": any(bool(row["lost_atoms_or_error"]) for row in items),
                "mean_final_msd_xy_a2": float(np.mean(msd)),
                "std_final_msd_xy_a2": float(np.std(msd, ddof=1)) if len(msd) > 1 else 0.0,
                "mean_diffusion_xy_cm2_s_short": float(np.mean(dxy)),
                "std_diffusion_xy_cm2_s_short": float(np.std(dxy, ddof=1)) if len(dxy) > 1 else 0.0,
            }
        )
    return out


def plot_mace(improvements: list[dict[str, object]], output_dir: Path) -> None:
    if plt is None:
        return
    rows = [row for row in improvements if row["split"] == "test" and row["family"] != "ALL"]
    if not rows:
        return
    labels = [str(row["family"]) for row in rows]
    x = np.arange(len(rows))
    width = 0.38
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - width / 2, [float(row["foundation_force_rmse_mev_a"]) for row in rows], width, label="Foundation")
    ax.bar(x + width / 2, [float(row["finetuned_force_rmse_mev_a"]) for row in rows], width, label="Fine-tuned")
    ax.set_ylabel("Force RMSE (meV/A)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "mace_test_force_rmse_comparison.png", dpi=200)
    plt.close(fig)


def plot_md(md_rows: list[dict[str, object]], traces: list[dict[str, object]], output_dir: Path) -> None:
    if plt is None:
        return
    if traces:
        fig, ax = plt.subplots(figsize=(8, 5))
        grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
        for row in traces:
            grouped[(str(row["case"]), str(row["seed"]))].append(row)
        for (case, seed), items in sorted(grouped.items()):
            items = sorted(items, key=lambda row: float(row["time_ps"]))
            ax.plot(
                [float(row["time_ps"]) for row in items],
                [float(row["msd_xy_a2"]) for row in items],
                label=f"{case} {seed}",
                alpha=0.65,
                linewidth=1.0,
            )
        ax.set_xlabel("Time (ps)")
        ax.set_ylabel("Li MSD xy (A^2)")
        ax.legend(fontsize=6, ncol=2)
        fig.tight_layout()
        fig.savefig(output_dir / "review_md_msd_xy_traces.png", dpi=200)
        plt.close(fig)

    agg = aggregate_md(md_rows)
    if agg:
        labels = [str(row["case"]) for row in agg]
        x = np.arange(len(agg))
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(x, [float(row["mean_diffusion_xy_cm2_s_short"]) for row in agg])
        ax.set_ylabel("Short-window Dxy (cm^2/s)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        fig.tight_layout()
        fig.savefig(output_dir / "review_md_short_diffusion_xy.png", dpi=200)
        plt.close(fig)


def write_markdown(
    output_dir: Path,
    mace_rows: list[dict[str, object]],
    improvements: list[dict[str, object]],
    committee_rows: list[dict[str, object]],
    md_rows: list[dict[str, object]],
    md_agg: list[dict[str, object]],
) -> None:
    def fmt(value: object, digits: int = 3) -> str:
        try:
            number = float(value)
        except Exception:  # noqa: BLE001
            return str(value)
        if math.isnan(number):
            return "nan"
        return f"{number:.{digits}g}"

    all_test = [row for row in improvements if row["split"] == "test" and row["family"] == "ALL"]
    lines = [
        "# Reviewer GPU Results Analysis",
        "",
        "## MACE Evaluation",
        "",
    ]
    if all_test:
        row = all_test[0]
        lines.append(
            "- Test-set force RMSE improved from "
            f"{fmt(row['foundation_force_rmse_mev_a'])} to {fmt(row['finetuned_force_rmse_mev_a'])} meV/A "
            f"({fmt(row['force_rmse_reduction_pct'])}% reduction)."
        )
        lines.append(
            "- Test-set energy RMSE changed from "
            f"{fmt(row['foundation_energy_rmse_mev_atom'])} to {fmt(row['finetuned_energy_rmse_mev_atom'])} meV/atom."
        )
    lines.extend(
        [
            "",
            "## Committee",
            "",
            f"- Completed seed models: {sum(1 for row in committee_rows if row['completed'])}/{len(committee_rows)}.",
            "- Validation force RMSE by seed: "
            + ", ".join(f"{row['seed']}={fmt(row['valid_force_rmse_mev_a'])} meV/A" for row in committee_rows),
            "",
            "## 100 ps Review MD",
            "",
            f"- Completed 100 ps runs: {sum(1 for row in md_rows if row['completed_100ps'])}/{len(md_rows)}.",
            f"- Runs with LAMMPS ERROR/Lost atoms/NaN: {sum(1 for row in md_rows if row['lost_atoms_or_error'])}.",
            "- Short-window Dxy estimates are diagnostics from 100 ps runs, not converged diffusion coefficients.",
            "",
            "| Case | seeds | final MSDxy A^2 mean | Dxy short cm^2/s mean |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in md_agg:
        lines.append(
            f"| {row['case']} | {row['n_seeds']} | {fmt(row['mean_final_msd_xy_a2'])} | "
            f"{fmt(row['mean_diffusion_xy_cm2_s_short'])} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- These GPU results address reviewer requests for held-out MACE validation, committee uncertainty diagnostics, and unwrapped-coordinate MD stability.",
            "- The 100 ps MD trajectories are enough to document stable unwrapped-coordinate pilots across 5 structures x 3 seeds, but are too short for a final converged diffusion coefficient.",
            "- Final migration-barrier claims still require the CPU CI-NEB jobs.",
        ]
    )
    (output_dir / "REVIEWER_GPU_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.input_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    mace_rows, improvements = parse_mace_eval(root)
    committee_rows = parse_committee(root)
    md_rows, traces = parse_md(root)
    md_agg = aggregate_md(md_rows)

    write_csv(output_dir / "mace_eval_summary.csv", mace_rows)
    write_csv(output_dir / "mace_eval_improvements.csv", improvements)
    write_csv(output_dir / "committee_summary.csv", committee_rows)
    write_csv(output_dir / "review_md_runs.csv", md_rows)
    write_csv(output_dir / "review_md_aggregate.csv", md_agg)
    write_csv(output_dir / "review_md_msd_traces_sampled.csv", traces)
    plot_mace(improvements, output_dir)
    plot_md(md_rows, traces, output_dir)
    write_markdown(output_dir, mace_rows, improvements, committee_rows, md_rows, md_agg)

    manifest = {
        "input_root": str(root),
        "output_dir": str(output_dir),
        "counts": {
            "mace_eval_rows": len(mace_rows),
            "mace_improvement_rows": len(improvements),
            "committee_models": len(committee_rows),
            "md_runs_100ps": len(md_rows),
            "md_aggregate_cases": len(md_agg),
        },
        "files": sorted(path.name for path in output_dir.iterdir() if path.is_file()),
    }
    (output_dir / "reviewer_gpu_analysis_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(output_dir / "REVIEWER_GPU_ANALYSIS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
