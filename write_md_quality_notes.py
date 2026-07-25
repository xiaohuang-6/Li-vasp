#!/usr/bin/env python3
"""Write quality notes for short MD outputs in the two-day rush package."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results/two_day_rush")
    parser.add_argument("--output", default="results/two_day_rush/MD_QUALITY_NOTES.md")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fnum(value: str | float, digits: int = 2) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def thermo_stats(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, float]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("case", ""), row.get("target_temperature_k", ""), row.get("target_steps", ""))].append(row)
    stats: dict[tuple[str, str, str], dict[str, float]] = {}
    for key, items in grouped.items():
        items = sorted(items, key=lambda item: int(float(item["step"])))
        temps = [float(item["temperature_k"]) for item in items]
        stats[key] = {
            "last_step": float(items[-1]["step"]),
            "last_temp": float(items[-1]["temperature_k"]),
            "max_temp": max(temps),
            "min_temp": min(temps),
        }
    return stats


def flag_summary(row: dict[str, str], stats: dict[str, float] | None) -> list[str]:
    flags: list[str] = []
    target = float(row.get("target_temperature_k") or 0.0)
    completed = str(row.get("completed_expected_steps", "")).lower() == "true"
    drift = row.get("total_energy_drift_ev_atom_assuming_last_natoms", "")
    try:
        abs_drift = abs(float(drift))
    except ValueError:
        abs_drift = 0.0
    if not completed:
        flags.append("incomplete")
    if stats and target > 0:
        if stats["max_temp"] > max(target + 300.0, 1.75 * target):
            flags.append("large temperature excursion")
        if target <= 500 and stats["last_temp"] > target + 300.0:
            flags.append("hot at latest frame")
    if abs_drift > 0.10:
        flags.append("large energy drift")
    return flags or ["usable short-run check"]


def write_section(lines: list[str], title: str, summary_rows: list[dict[str, str]], thermo_rows: list[dict[str, str]]) -> None:
    lines.extend(["", f"## {title}", ""])
    if not summary_rows:
        lines.append("No summary available yet.")
        return
    stats = thermo_stats(thermo_rows)
    lines.extend(
        [
            "| Case | Target K | Last step | Last T K | Max T K | Drift eV/atom | Flags |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in sorted(summary_rows, key=lambda item: (item.get("case", ""), item.get("target_temperature_k", ""))):
        key = (row.get("case", ""), row.get("target_temperature_k", ""), row.get("target_steps", ""))
        stat = stats.get(key)
        flags = flag_summary(row, stat)
        lines.append(
            f"| {row.get('case', '')} | {fnum(row.get('target_temperature_k', ''), 0)} | "
            f"{row.get('last_step', '')} | "
            f"{fnum(stat['last_temp'], 1) if stat else 'n/a'} | "
            f"{fnum(stat['max_temp'], 1) if stat else 'n/a'} | "
            f"{fnum(row.get('total_energy_drift_ev_atom_assuming_last_natoms', ''), 3)} | "
            f"{'; '.join(flags)} |"
        )


def main() -> int:
    args = parse_args()
    results_dir = Path(args.results_dir)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# MD Quality Notes",
        "",
        "This file separates usable short-run stability evidence from high-temperature or currently incomplete "
        "trajectory evidence. It is generated from the current MD summary and thermo CSV files.",
        "",
        "Interpretation rule: completed 400 K / 1 ps runs are acceptable as conservative stability checks; "
        "800 K runs and any 400 K trajectories with large temperature or energy excursions should be discussed "
        "as perturbation/reconstruction evidence, not as equilibrium diffusion data.",
    ]

    write_section(
        lines,
        "400 K / 1 ps completed backup",
        read_csv(results_dir / "md_fast" / "md_summary.csv"),
        read_csv(results_dir / "md_fast" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "400 K / 2 ps stable subset excluding B1",
        read_csv(results_dir / "md_400k_stable2ps" / "md_summary.csv"),
        read_csv(results_dir / "md_400k_stable2ps" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "400 K / 2.5 ps stable subset excluding B1",
        read_csv(results_dir / "md_400k_stable2p5ps" / "md_summary.csv"),
        read_csv(results_dir / "md_400k_stable2p5ps" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "400 K / 2.7 ps stable subset excluding B1",
        read_csv(results_dir / "md_400k_stable2p7ps" / "md_summary.csv"),
        read_csv(results_dir / "md_400k_stable2p7ps" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "400 K / 2.8 ps stable subset excluding B1",
        read_csv(results_dir / "md_400k_stable2p8ps" / "md_summary.csv"),
        read_csv(results_dir / "md_400k_stable2p8ps" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "Current longest 400 K stable subset excluding B1",
        read_csv(results_dir / "md_400k_stable_current" / "md_summary.csv"),
        read_csv(results_dir / "md_400k_stable_current" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "800 K / 2 ps perturbation",
        read_csv(results_dir / "md_800k" / "md_summary.csv"),
        read_csv(results_dir / "md_800k" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "Current partial 400 K / 10 ps and combined progress",
        read_csv(results_dir / "md_partial" / "md_summary.csv"),
        read_csv(results_dir / "md_partial" / "md_thermo.csv"),
    )
    write_section(
        lines,
        "Final combined MD output",
        read_csv(results_dir / "md" / "md_summary.csv"),
        read_csv(results_dir / "md" / "md_thermo.csv"),
    )

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
