#!/usr/bin/env python3
"""Refresh the current longest clean 400 K MD subset.

The long 400 K array can keep running while diagnostic artifacts are prepared.
This helper finds the latest common thermo step among the selected stable cases
and reruns ``analyze_short_md.py`` with ``--max-step`` so the results package has
a moving, conservative MD figure that does not wait for the full 10 ps array.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


THERMO_RE = re.compile(r"^\s*(\d+)\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+\s+[-+0-9.eE]+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default="lammps_logs/two_day_md")
    parser.add_argument("--traj-dir", default="trajectories/two_day_md")
    parser.add_argument("--results-dir", default="results/two_day_rush")
    parser.add_argument("--log-glob", default="*_400K_10000steps.log")
    parser.add_argument("--traj-glob", default="*_400K_10000steps.lammpstrj")
    parser.add_argument("--exclude-cases", default="B1_Monovacancy")
    parser.add_argument("--min-step", type=int, default=1000)
    parser.add_argument("--also-write-step-label", action="store_true")
    return parser.parse_args()


def case_from_name(path: Path) -> str:
    return path.name.replace("_400K_10000steps.log", "")


def last_thermo_step(path: Path) -> int | None:
    last_step: int | None = None
    for line in path.read_text(errors="replace").splitlines():
        match = THERMO_RE.match(line)
        if match:
            last_step = int(match.group(1))
    return last_step


def ps_label(step: int) -> str:
    value = step / 1000.0
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


def run_analysis(output_dir: Path, max_step: int, args: argparse.Namespace) -> None:
    cmd = [
        sys.executable,
        "analyze_short_md.py",
        "--log-dir",
        args.log_dir,
        "--log-glob",
        args.log_glob,
        "--traj-dir",
        args.traj_dir,
        "--traj-glob",
        args.traj_glob,
        "--output-dir",
        str(output_dir),
        "--expected-steps",
        str(max_step),
        "--max-step",
        str(max_step),
        "--exclude-cases",
        args.exclude_cases,
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    args = parse_args()
    excluded = {item.strip() for item in args.exclude_cases.split(",") if item.strip()}
    steps: dict[str, int] = {}
    for path in sorted(Path(args.log_dir).glob(args.log_glob)):
        case = case_from_name(path)
        if case in excluded:
            continue
        step = last_thermo_step(path)
        if step is not None:
            steps[case] = step

    if not steps:
        print("No stable-case thermo rows found.", file=sys.stderr)
        return 1
    common_step = min(steps.values())
    if common_step < args.min_step:
        print(f"Common stable window {common_step} is below --min-step {args.min_step}.", file=sys.stderr)
        return 1

    results_dir = Path(args.results_dir)
    current_dir = results_dir / "md_400k_stable_current"
    run_analysis(current_dir, common_step, args)
    print(f"Current stable 400 K window: {common_step} steps ({common_step / 1000.0:.3f} ps)")
    for case, step in sorted(steps.items()):
        print(f"  {case}: {step} steps")

    if args.also_write_step_label:
        labeled_dir = results_dir / f"md_400k_stable{ps_label(common_step)}ps"
        run_analysis(labeled_dir, common_step, args)
        print(f"Also wrote labeled stable-window directory: {labeled_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
