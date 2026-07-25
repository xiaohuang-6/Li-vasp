#!/usr/bin/env python3
"""Write a compact report-results brief from regenerated analysis outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results/two_day_rush")
    parser.add_argument("--output", default="results/two_day_rush/REPORT_RESULTS_BRIEF.md")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt(value: str, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def best_sites(site_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[str, dict[str, str]] = {}
    for row in site_rows:
        family = row.get("family", "")
        if not family:
            continue
        current = best.get(family)
        if current is None or float(row.get("rel_to_site_min_ev", "inf")) < float(current.get("rel_to_site_min_ev", "inf")):
            best[family] = row
    return [best[key] for key in sorted(best)]


def md_status(results_dir: Path) -> list[str]:
    rows = []
    for label, subdir in [
        ("partial", results_dir / "md_partial"),
        ("fast_1ps", results_dir / "md_fast"),
        ("stable_400K_2ps_no_B1", results_dir / "md_400k_stable2ps"),
        ("stable_400K_2p5ps_no_B1", results_dir / "md_400k_stable2p5ps"),
        ("stable_400K_2p7ps_no_B1", results_dir / "md_400k_stable2p7ps"),
        ("stable_400K_2p8ps_no_B1", results_dir / "md_400k_stable2p8ps"),
        ("stable_400K_current_no_B1", results_dir / "md_400k_stable_current"),
        ("highT_800K_2ps", results_dir / "md_800k"),
        ("final", results_dir / "md"),
    ]:
        summary = subdir / "md_summary.csv"
        thermo = subdir / "md_temperature_energy.png"
        msd = subdir / "md_li_xy_msd.png"
        if summary.exists():
            rows.append(f"- `{label}`: available at `{subdir}`; summary/table and plots present: {thermo.exists() and msd.exists()}")
        else:
            rows.append(f"- `{label}`: not available yet")
    return rows


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    path_rows = read_csv(results_dir / "path_barriers.csv")
    site_rows = read_csv(results_dir / "site_energy_rankings.csv")
    error_rows = read_csv(results_dir / "mace_error_table_final.csv")
    dataset_rows = read_csv(results_dir / "dataset_frames.csv")

    family_counts: dict[str, int] = {}
    for row in dataset_rows:
        if row.get("split") != "all":
            continue
        family = row.get("family", "unknown")
        family_counts[family] = family_counts.get(family, 0) + 1

    lines = [
        "# Report Results Brief",
        "",
        "## Data Package",
        f"- Results directory: `{results_dir}`",
        f"- Total MACE frames: {sum(family_counts.values()) if family_counts else 'n/a'}",
    ]
    if family_counts:
        lines.append("- Family frame counts: " + ", ".join(f"{key}={family_counts[key]}" for key in sorted(family_counts)))

    lines.extend(["", "## MACE Validation"])
    if error_rows:
        for row in error_rows:
            if row.get("section") == "train_valid":
                lines.append(
                    f"- {row['config_type']}: E RMSE {fmt(row['rmse_e_mev_atom'], 1)} meV/atom; "
                    f"F RMSE {fmt(row['rmse_f_mev_a'], 1)} meV/A"
                )
        lines.append(f"- Full final error table: `{results_dir / 'mace_error_table_final.csv'}`")
    else:
        lines.append("- MACE error table missing.")

    lines.extend(["", "## Lowest-Energy Li Sites", "", "| Family | Site | Relative energy (eV) |", "|---|---:|---:|"])
    for row in best_sites(site_rows):
        lines.append(f"| {row['family']} | {row['label']} | {fmt(row['rel_to_site_min_ev'])} |")

    lines.extend(
        [
            "",
            "## Approximate Diffusion Barriers",
            "",
            "| Family | Path | Barrier from path minimum (eV) | Delta E end-start (eV) |",
            "|---|---|---:|---:|",
        ]
    )
    for row in sorted(path_rows, key=lambda item: (item.get("family", ""), item.get("path_id", ""))):
        path = f"{row.get('path_id', '')}: {row.get('path_start', '')} -> {row.get('path_end', '')}"
        lines.append(
            f"| {row.get('family', '')} | {path} | "
            f"{fmt(row.get('barrier_from_path_min_ev', ''))} | "
            f"{fmt(row.get('delta_e_end_minus_start_ev', ''))} |"
        )

    lines.extend(["", "## MD Status"])
    lines.extend(md_status(results_dir))
    lines.extend(
        [
            "",
            "## Recommended Figure Set",
            "- `dataset_family_counts.png`: dataset composition.",
            "- `training_curve.png`: MACE fine-tuning convergence.",
            "- `site_energy_rankings.png`: Li adsorption-site energetics.",
            "- `path_profiles.png`: Li path energy profiles and approximate barriers.",
            "- `md_fast/md_temperature_energy.png` or `md/md_temperature_energy.png`: short MLMD stability.",
            "- `md_fast/md_li_xy_msd.png` or `md/md_li_xy_msd.png`: short-run Li displacement.",
            "- `md_400k_stable2ps/md_temperature_energy.png`: 400 K stable subset excluding unstable B1.",
            "- `md_400k_stable2p5ps/md_temperature_energy.png`: longer 400 K stable subset excluding unstable B1.",
            "- `md_400k_stable2p7ps/md_temperature_energy.png`: longer 400 K stable subset excluding unstable B1.",
            "- `md_400k_stable2p8ps/md_temperature_energy.png`: longer 400 K stable subset excluding unstable B1.",
            "- `md_400k_stable_current/md_temperature_energy.png`: latest refreshed stable 400 K subset excluding unstable B1.",
            "- `md_800k/md_temperature_energy.png`: high-temperature perturbation check.",
            "",
            "## Reporting Caveat",
            "The available MD is short-time MLMD stability and qualitative mobility evidence. "
            "Do not claim converged ns-scale diffusion coefficients from these runs.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
