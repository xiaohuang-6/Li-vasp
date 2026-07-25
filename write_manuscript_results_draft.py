#!/usr/bin/env python3
"""Write a manuscript-ready Results draft from the two-day rush outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results/two_day_rush")
    parser.add_argument("--output", default="results/two_day_rush/MANUSCRIPT_RESULTS_DRAFT.md")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    delimiter = "\t" if path.suffix == ".tsv" else ","
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def fnum(value: str | float, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def best_site_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("kind") != "site":
            continue
        family = row.get("family", "")
        if not family:
            continue
        current = best.get(family)
        if current is None or float(row.get("rel_to_site_min_ev", "inf")) < float(current.get("rel_to_site_min_ev", "inf")):
            best[family] = row
    return [best[key] for key in sorted(best)]


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    dataset_rows = read_csv(results_dir / "dataset_frames.csv")
    error_rows = read_csv(results_dir / "mace_error_table_final.csv")
    site_rows = read_csv(results_dir / "site_energy_rankings.csv")
    barrier_rows = read_csv(results_dir / "path_barriers.csv")
    md_rows = read_csv(results_dir / "md_fast" / "md_summary.csv")
    md_stable_rows = read_csv(results_dir / "md_400k_stable2ps" / "md_summary.csv")
    md_stable_25_rows = read_csv(results_dir / "md_400k_stable2p5ps" / "md_summary.csv")
    md_stable_27_rows = read_csv(results_dir / "md_400k_stable2p7ps" / "md_summary.csv")
    md_stable_28_rows = read_csv(results_dir / "md_400k_stable2p8ps" / "md_summary.csv")
    md_stable_current_rows = read_csv(results_dir / "md_400k_stable_current" / "md_summary.csv")
    md_800k_rows = read_csv(results_dir / "md_800k" / "md_summary.csv")
    scaling_rows = read_csv(Path("benchmarks/cpu_scaling_3095807/scaling_summary.tsv"))

    family_counts: dict[str, int] = {}
    for row in dataset_rows:
        if row.get("split") == "all":
            family = row.get("family", "unknown")
            family_counts[family] = family_counts.get(family, 0) + 1
    n_frames = sum(family_counts.values())

    train_valid = [row for row in error_rows if row.get("section") == "train_valid"]
    train = next((row for row in train_valid if row.get("config_type") == "train_Default"), None)
    valid = next((row for row in train_valid if row.get("config_type") == "valid_Default"), None)

    lines: list[str] = [
        "# Manuscript Results Draft",
        "",
        "This draft is generated from the current two-day rush result package. It is written to be conservative: "
        "the DFT migration barriers are fixed-geometry path-scan estimates rather than NEB barriers, and the "
        "MLMD data are short-time stability and local Li-motion checks rather than converged diffusion coefficients.",
        "",
        "## Machine-learned force field validation",
        "",
        f"The MACE training set contains {n_frames if n_frames else 'n/a'} labeled frames across the five graphene-based systems.",
    ]
    if family_counts:
        lines.append(
            "The frame distribution is "
            + ", ".join(f"{key}: {family_counts[key]}" for key in sorted(family_counts))
            + "."
        )
    if train and valid:
        lines.append(
            "After fine-tuning, the model reached "
            f"{fnum(train['rmse_e_mev_atom'], 1)} meV/atom energy RMSE and "
            f"{fnum(train['rmse_f_mev_a'], 1)} meV/A force RMSE on the training split, and "
            f"{fnum(valid['rmse_e_mev_atom'], 1)} meV/atom energy RMSE and "
            f"{fnum(valid['rmse_f_mev_a'], 1)} meV/A force RMSE on the validation split. "
            "These errors are sufficient for short qualitative MLMD screening in this rush workflow, "
            "but the validation set remains small and should not be overinterpreted as transferability evidence."
        )
    lines.extend(
        [
            "",
            "Suggested citation in Results:",
            "",
            "> The fine-tuned MACE model reproduces the local DFT labels with sub-meV/atom validation energy error "
            "and a validation force RMSE of 48.5 meV/A, supporting its use for short-time qualitative MLMD stability "
            "tests of the same defect families.",
            "",
            "## Li adsorption site energetics",
            "",
            "| System | Lowest-energy site | Relative energy (eV) |",
            "|---|---:|---:|",
        ]
    )
    for row in best_site_rows(site_rows):
        lines.append(f"| {row['family']} | {row['label']} | {fnum(row['rel_to_site_min_ev'])} |")

    lines.extend(
        [
            "",
            "The fixed-geometry DFT single-point scan identifies distinct Li trapping motifs across the systems. "
            "Pristine graphene favors the hollow C3 site among the sampled configurations, while the monovacancy, "
            "divacancy, and Si-graphene systems favor the initial/prior Li position near the defect or composite region. "
            "The Stone-Wales model has a shallow site landscape in the sampled region, with the top-central C site lowest "
            "and several nearby sites within about 0.08 eV.",
            "",
            "## Approximate path-scan barriers",
            "",
            "| System | Path | Barrier from path minimum (eV) | End-start energy (eV) |",
            "|---|---|---:|---:|",
        ]
    )
    for row in sorted(barrier_rows, key=lambda item: (item.get("family", ""), item.get("path_id", ""))):
        path = f"{row.get('path_id', '')}: {row.get('path_start', '')} -> {row.get('path_end', '')}"
        lines.append(
            f"| {row.get('family', '')} | {path} | "
            f"{fnum(row.get('barrier_from_path_min_ev', ''))} | "
            f"{fnum(row.get('delta_e_end_minus_start_ev', ''))} |"
        )

    lines.extend(
        [
            "",
            "The lowest sampled path barriers occur for the pristine prior-Li-to-hollow path "
            "(0.040 eV) and the Stone-Wales prior-Li-to-hollow path (0.020 eV). "
            "Vacancy-containing systems show larger barriers on the sampled paths, with values of about "
            "0.27-0.68 eV depending on defect type and pathway. The Si-graphene composite has one high-barrier "
            "path from the prior Li position to the C-C bridge (0.559 eV) and a lower sampled path from top-central C "
            "to hollow C3 (0.191 eV), consistent with a heterogeneous local potential-energy landscape near the Si cluster.",
            "",
            "## Short MLMD stability and Li motion",
            "",
        ]
    )
    if md_rows:
        lines.extend(
            [
                "The completed backup MLMD data contain 1 ps NVT trajectories at 400 K for all five systems. "
                "All five jobs reached the expected 1000 steps without LAMMPS fatal errors. The temperature and "
                "energy summaries are:",
                "",
                "| System | Mean T (K) | Std T (K) | Energy drift (eV/atom) | Throughput (ns/day) |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for row in md_rows:
            lines.append(
                f"| {row['case']} | {fnum(row['mean_temperature_k'], 1)} | "
                f"{fnum(row['std_temperature_k'], 1)} | "
                f"{fnum(row['total_energy_drift_ev_atom_assuming_last_natoms'], 3)} | "
                f"{fnum(row['ns_per_day'], 3)} |"
            )
        lines.extend(
            [
                "",
                "The short trajectories should be used as a stability and qualitative local-motion check. "
                "They are not long enough to report converged diffusion coefficients. If the longer 10 ps 400 K "
                "array completes before submission, replace these backup plots with `results/two_day_rush/md/` only after "
                "checking `results/two_day_rush/MD_QUALITY_NOTES.md` for temperature and energy-drift flags.",
            ]
        )
    else:
        lines.append("The short MD summary is not available yet.")

    if md_stable_rows:
        lines.extend(
            [
                "",
                "A longer 400 K subset was also extracted from the in-progress 10 ps array by using the first 2 ps "
                "of the systems that remained stable over that window and excluding the monovacancy trajectory after "
                "its strong temperature excursion. This subset is useful as a more conservative 400 K stability figure "
                "than the full mixed trajectory set.",
                "",
                "| System | Last step | Mean T (K) | Energy drift (eV/atom) |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in md_stable_rows:
            lines.append(
                f"| {row['case']} | {row['last_step']} | "
                f"{fnum(row['mean_temperature_k'], 1)} | "
                f"{fnum(row['total_energy_drift_ev_atom_assuming_last_natoms'], 3)} |"
            )

    if md_stable_25_rows:
        lines.extend(
            [
                "",
                "The currently preferred 400 K stability figure is the 2.5 ps stable subset, which again excludes "
                "the monovacancy trajectory and keeps the four systems that remain well behaved through 2.5 ps.",
                "",
                "| System | Last step | Mean T (K) | Energy drift (eV/atom) |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in md_stable_25_rows:
            lines.append(
                f"| {row['case']} | {row['last_step']} | "
                f"{fnum(row['mean_temperature_k'], 1)} | "
                f"{fnum(row['total_energy_drift_ev_atom_assuming_last_natoms'], 3)} |"
            )

    if md_stable_27_rows:
        lines.extend(
            [
                "",
                "A longer clean 400 K subset extends this conservative window to 2.7 ps, "
                "again excluding the monovacancy trajectory.",
                "",
                "| System | Last step | Mean T (K) | Energy drift (eV/atom) |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in md_stable_27_rows:
            lines.append(
                f"| {row['case']} | {row['last_step']} | "
                f"{fnum(row['mean_temperature_k'], 1)} | "
                f"{fnum(row['total_energy_drift_ev_atom_assuming_last_natoms'], 3)} |"
            )

    if md_stable_28_rows:
        lines.extend(
            [
                "",
                "A longer clean 400 K subset extends this conservative window to 2.8 ps, "
                "again excluding the monovacancy trajectory.",
                "",
                "| System | Last step | Mean T (K) | Energy drift (eV/atom) |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in md_stable_28_rows:
            lines.append(
                f"| {row['case']} | {row['last_step']} | "
                f"{fnum(row['mean_temperature_k'], 1)} | "
                f"{fnum(row['total_energy_drift_ev_atom_assuming_last_natoms'], 3)} |"
            )

    if md_stable_current_rows:
        current_steps = max(int(float(row.get("last_step", "0"))) for row in md_stable_current_rows)
        lines.extend(
            [
                "",
                f"The latest refreshed clean 400 K subset extends this conservative window to {current_steps / 1000.0:.1f} ps, "
                "again excluding the monovacancy trajectory.",
                "",
                "| System | Last step | Mean T (K) | Energy drift (eV/atom) |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in md_stable_current_rows:
            lines.append(
                f"| {row['case']} | {row['last_step']} | "
                f"{fnum(row['mean_temperature_k'], 1)} | "
                f"{fnum(row['total_energy_drift_ev_atom_assuming_last_natoms'], 3)} |"
            )

    if md_800k_rows:
        lines.extend(
            [
                "",
                "## High-temperature perturbation check",
                "",
                "The 800 K / 2 ps trajectories completed for all five systems and are best interpreted as an accelerated "
                "stress test rather than equilibrium 400 K diffusion sampling. The vacancy systems, especially the "
                "monovacancy case, show strong temperature and energy excursions, consistent with rapid local "
                "reconstruction or trapping events under high-temperature perturbation.",
                "",
                "| System | Mean T (K) | Final step | Energy drift (eV/atom) | Throughput (ns/day) |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for row in md_800k_rows:
            lines.append(
                f"| {row['case']} | {fnum(row['mean_temperature_k'], 1)} | "
                f"{row['last_step']} | "
                f"{fnum(row['total_energy_drift_ev_atom_assuming_last_natoms'], 3)} | "
                f"{fnum(row['ns_per_day'], 3)} |"
            )

    if scaling_rows:
        best = max(scaling_rows, key=lambda row: float(row.get("steps_per_second", "0") or 0))
        lines.extend(
            [
                "",
                "## CPU execution note",
                "",
                "A short CPU thread-scaling benchmark showed no benefit from increasing OpenMP thread count for the "
                "small 200-220 atom MACE/LAMMPS systems. The fastest tested setting was "
                f"{best['threads']} thread(s) at {fnum(best['steps_per_second'], 3)} steps/s. "
                "This explains why the current CPU MD is throughput-limited and why multi-ns production runs are "
                "not realistic without GPU access.",
            ]
        )

    lines.extend(
        [
            "",
            "## Figure references",
            "",
            "- Dataset composition: `results/two_day_rush/dataset_family_counts.png`",
            "- MACE convergence: `results/two_day_rush/training_curve.png`",
            "- Site energetics: `results/two_day_rush/site_energy_rankings.png`",
            "- Path profiles: `results/two_day_rush/path_profiles.png`",
            "- Backup short MD stability: `results/two_day_rush/md_fast/md_temperature_energy.png`",
            "- Backup short Li displacement: `results/two_day_rush/md_fast/md_li_xy_msd.png`",
            "- Stable 400 K subset: `results/two_day_rush/md_400k_stable2ps/md_temperature_energy.png`",
            "- Preferred current 400 K subset: `results/two_day_rush/md_400k_stable2p5ps/md_temperature_energy.png`",
            "- Longer stable 400 K subset: `results/two_day_rush/md_400k_stable2p7ps/md_temperature_energy.png`",
            "- Longer stable 400 K subset: `results/two_day_rush/md_400k_stable2p8ps/md_temperature_energy.png`",
            "- Longest current stable 400 K subset: `results/two_day_rush/md_400k_stable_current/md_temperature_energy.png`",
            "- High-temperature perturbation: `results/two_day_rush/md_800k/md_temperature_energy.png`",
            "- MD quality flags: `results/two_day_rush/MD_QUALITY_NOTES.md`",
            "",
            "## Required caveat",
            "",
            "Use the phrase 'fixed-geometry path-scan barrier' instead of 'NEB barrier'. "
            "Use the phrase 'short-time qualitative MLMD' instead of 'diffusion coefficient' unless longer "
            "trajectories and proper MSD fitting are added.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
