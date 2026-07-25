#!/usr/bin/env python3
"""Create a manifest for the regenerated report result package."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="results/two_day_rush/RESULTS_MANIFEST.json")
    return parser.parse_args()


def file_record(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def command_output(cmd: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return ""
    return (result.stdout + result.stderr).strip()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    key_files = [
        "results/two_day_rush/REPORT_RESULTS_BRIEF.md",
        "results/two_day_rush/MD_QUALITY_NOTES.md",
        "results/two_day_rush/SUMMARY.md",
        "results/two_day_rush/dataset_summary.json",
        "results/two_day_rush/mace_error_table_final.csv",
        "results/two_day_rush/site_energy_rankings.csv",
        "results/two_day_rush/path_barriers.csv",
        "results/two_day_rush/path_profiles.csv",
        "results/two_day_rush/dataset_family_counts.png",
        "results/two_day_rush/training_curve.png",
        "results/two_day_rush/site_energy_rankings.png",
        "results/two_day_rush/path_profiles.png",
        "results/two_day_rush/md_partial/md_summary.csv",
        "results/two_day_rush/md_partial/md_temperature_energy.png",
        "results/two_day_rush/md_partial/md_li_xy_msd.png",
        "results/two_day_rush/md_fast/md_summary.csv",
        "results/two_day_rush/md_fast/md_temperature_energy.png",
        "results/two_day_rush/md_fast/md_li_xy_msd.png",
        "results/two_day_rush/md_400k_stable2ps/md_summary.csv",
        "results/two_day_rush/md_400k_stable2ps/md_temperature_energy.png",
        "results/two_day_rush/md_400k_stable2ps/md_li_xy_msd.png",
        "results/two_day_rush/md_400k_stable2p5ps/md_summary.csv",
        "results/two_day_rush/md_400k_stable2p5ps/md_temperature_energy.png",
        "results/two_day_rush/md_400k_stable2p5ps/md_li_xy_msd.png",
        "results/two_day_rush/md_400k_stable2p7ps/md_summary.csv",
        "results/two_day_rush/md_400k_stable2p7ps/md_temperature_energy.png",
        "results/two_day_rush/md_400k_stable2p7ps/md_li_xy_msd.png",
        "results/two_day_rush/md_400k_stable2p8ps/md_summary.csv",
        "results/two_day_rush/md_400k_stable2p8ps/md_temperature_energy.png",
        "results/two_day_rush/md_400k_stable2p8ps/md_li_xy_msd.png",
        "results/two_day_rush/md_400k_stable_current/md_summary.csv",
        "results/two_day_rush/md_400k_stable_current/md_temperature_energy.png",
        "results/two_day_rush/md_400k_stable_current/md_li_xy_msd.png",
        "results/two_day_rush/md_800k/md_summary.csv",
        "results/two_day_rush/md_800k/md_temperature_energy.png",
        "results/two_day_rush/md_800k/md_li_xy_msd.png",
        "results/two_day_rush/md/md_summary.csv",
        "results/two_day_rush/md/md_temperature_energy.png",
        "results/two_day_rush/md/md_li_xy_msd.png",
        "README_TWO_DAY_RUSH.md",
        "rapid_results_analysis.py",
        "analyze_short_md.py",
        "write_paper_results_brief.py",
        "write_md_quality_notes.py",
        "refresh_current_stable_md.py",
    ]
    lammps_inputs = sorted(str(path) for path in (root / "data/lammps").glob("two_day_*_2x2x1.data"))
    lammps_summaries = sorted(str(path) for path in (root / "data/lammps").glob("two_day_*_2x2x1.summary.json"))
    logs = sorted(str(path) for path in (root / "lammps_logs/two_day_md").glob("*.log"))
    trajectories = sorted(str(path) for path in (root / "trajectories/two_day_md").glob("*.lammpstrj"))

    manifest = {
        "project_root": str(root),
        "status_commands": {
            "squeue": command_output(
                ["squeue", "-u", "xh121", "-o", "%.18i %.9P %.28j %.8u %.2t %.12M %.6D %R"],
                root,
            ),
            "sacct": command_output(
                [
                    "sacct",
                    "-j",
                    "3095801,3095808,3095788,3095794,3095864,3095807,3095863",
                    "--format=JobID,JobName%24,Partition,State,ExitCode,Elapsed,AllocCPUS,MaxRSS%14,NodeList%24",
                    "-P",
                ],
                root,
            ),
            "postprocess_job": command_output(["scontrol", "show", "job", "3095864"], root),
        },
        "key_files": [file_record(root / path) for path in key_files],
        "lammps_inputs": [file_record(Path(path)) for path in lammps_inputs],
        "lammps_summaries": [file_record(Path(path)) for path in lammps_summaries],
        "md_logs": [file_record(Path(path)) for path in logs],
        "md_trajectories": [file_record(Path(path)) for path in trajectories],
        "report_recommended_order": [
            "dataset_family_counts.png",
            "training_curve.png",
            "mace_error_table_final.csv",
            "site_energy_rankings.png",
            "path_profiles.png",
            "md_fast/md_temperature_energy.png or md/md_temperature_energy.png",
            "md_fast/md_li_xy_msd.png or md/md_li_xy_msd.png",
            "md_400k_stable2ps/md_temperature_energy.png",
            "md_400k_stable2p5ps/md_temperature_energy.png",
            "md_400k_stable2p7ps/md_temperature_energy.png",
            "md_400k_stable2p8ps/md_temperature_energy.png",
            "md_400k_stable_current/md_temperature_energy.png",
            "md_800k/md_temperature_energy.png",
        ],
        "limitations": [
            "MACE ASE parity is skipped on CPU because .model loading triggers a CUDA driver check.",
            "MD outputs are short-time stability and qualitative Li mobility evidence, not converged ns-scale diffusion coefficients.",
        ],
    }
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
