#!/usr/bin/env python3
"""Summarize short LAMMPS MLMD runs for diagnostic result figures."""

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
    r"^\s*(?P<step>\d+)\s+"
    r"(?P<time>[-+0-9.eE]+)\s+"
    r"(?P<temp>[-+0-9.eE]+)\s+"
    r"(?P<pe>[-+0-9.eE]+)\s+"
    r"(?P<ke>[-+0-9.eE]+)\s+"
    r"(?P<etotal>[-+0-9.eE]+)\s+"
    r"(?P<press>[-+0-9.eE]+)\s+"
    r"(?P<vol>[-+0-9.eE]+)\s*$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-dir", default="lammps_logs/two_day_md")
    parser.add_argument("--log-glob", default="*K_*steps.log")
    parser.add_argument("--traj-dir", default="trajectories/two_day_md")
    parser.add_argument("--traj-glob", default="*K_*steps.lammpstrj")
    parser.add_argument("--output-dir", default="results/two_day_rush/md")
    parser.add_argument("--expected-steps", type=int, default=10000)
    parser.add_argument("--include-cases", default="", help="Comma-separated case names to include.")
    parser.add_argument("--exclude-cases", default="", help="Comma-separated case names to exclude.")
    parser.add_argument("--max-step", type=int, default=None, help="Discard thermo/trajectory rows after this MD step.")
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def expand_globs(directory: Path, patterns: str) -> list[Path]:
    """Return de-duplicated paths for one or more comma-separated glob patterns."""
    paths: list[Path] = []
    seen: set[Path] = set()
    for pattern in (item.strip() for item in patterns.split(",")):
        if not pattern:
            continue
        for path in sorted(directory.glob(pattern)):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(path)
    return paths


def split_cases(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def keep_case(case: str, include_cases: set[str], exclude_cases: set[str]) -> bool:
    if include_cases and case not in include_cases:
        return False
    return case not in exclude_cases


def filter_rows(rows: list[dict[str, object]], include_cases: set[str], exclude_cases: set[str], max_step: int | None) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    for row in rows:
        if not keep_case(str(row.get("case", "")), include_cases, exclude_cases):
            continue
        if max_step is not None and int(row.get("step", 0)) > max_step:
            continue
        if max_step is not None:
            row = dict(row)
            row["target_steps"] = max_step
        filtered.append(row)
    return filtered


def meta_from_path(path: Path) -> tuple[str, float | None, int | None]:
    name = path.name
    match = re.match(r"(?P<case>.+)_(?P<temperature>[0-9.]+)K_(?P<nsteps>\d+)steps\.", name)
    if not match:
        return name.split(".")[0], None, None
    return match.group("case"), float(match.group("temperature")), int(match.group("nsteps"))


def case_from_path(path: Path) -> str:
    return meta_from_path(path)[0]


def parse_thermo(log_path: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    case, target_temperature, target_steps = meta_from_path(log_path)
    rows: list[dict[str, object]] = []
    performance = {}
    loop_re = re.compile(r"Loop time of\s+([0-9.eE+-]+).*for\s+(\d+)\s+steps\s+with\s+(\d+)\s+atoms")
    perf_re = re.compile(r"Performance:\s+([0-9.eE+-]+)\s+ns/day,\s+([0-9.eE+-]+)\s+hours/ns,\s+([0-9.eE+-]+)\s+timesteps/s")
    atoms_re = re.compile(r"^\s*(\d+)\s+atoms\s*$")
    for line in log_path.read_text(errors="replace").splitlines():
        atoms_match = atoms_re.match(line)
        if atoms_match and "natoms" not in performance:
            performance["natoms"] = int(atoms_match.group(1))
        match = THERMO_RE.match(line)
        if match:
            rows.append(
                {
                    "case": case,
                    "target_temperature_k": target_temperature if target_temperature is not None else "",
                    "target_steps": target_steps if target_steps is not None else "",
                    "step": int(match.group("step")),
                    "time_ps": float(match.group("time")),
                    "temperature_k": float(match.group("temp")),
                    "potential_energy_ev": float(match.group("pe")),
                    "kinetic_energy_ev": float(match.group("ke")),
                    "total_energy_ev": float(match.group("etotal")),
                    "pressure_bar": float(match.group("press")),
                    "volume_a3": float(match.group("vol")),
                }
            )
        loop = loop_re.search(line)
        if loop:
            performance.update(
                {
                    "loop_time_s": float(loop.group(1)),
                    "loop_steps": int(loop.group(2)),
                    "natoms": int(loop.group(3)),
                }
            )
        perf = perf_re.search(line)
        if perf:
            performance.update(
                {
                    "ns_per_day": float(perf.group(1)),
                    "hours_per_ns": float(perf.group(2)),
                    "timesteps_per_s": float(perf.group(3)),
                }
            )
    return rows, performance


def parse_lammpstrj(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    case, target_temperature, target_steps = meta_from_path(path)
    first_li: dict[int, np.ndarray] = {}
    current_step = None
    current_atoms = None
    current_fields: list[str] = []
    lines = path.read_text(errors="replace").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("ITEM: TIMESTEP"):
            current_step = int(lines[i + 1].strip())
            i += 2
            continue
        if line.startswith("ITEM: NUMBER OF ATOMS"):
            current_atoms = int(lines[i + 1].strip())
            i += 2
            continue
        if line.startswith("ITEM: ATOMS"):
            current_fields = line.split()[2:]
            idx = {name: pos for pos, name in enumerate(current_fields)}
            frame_li: dict[int, np.ndarray] = {}
            for atom_line in lines[i + 1 : i + 1 + int(current_atoms or 0)]:
                parts = atom_line.split()
                element = parts[idx["element"]] if "element" in idx else ""
                atom_type = parts[idx["type"]] if "type" in idx else ""
                if element != "Li" and atom_type != "2":
                    continue
                atom_id = int(parts[idx["id"]])
                pos = np.array([float(parts[idx["x"]]), float(parts[idx["y"]]), float(parts[idx["z"]])], dtype=float)
                frame_li[atom_id] = pos
                first_li.setdefault(atom_id, pos)
            if frame_li and current_step is not None:
                displacements = []
                for atom_id, pos in sorted(frame_li.items()):
                    disp = pos - first_li[atom_id]
                    displacements.append(disp)
                    rows.append(
                        {
                            "case": case,
                            "target_temperature_k": target_temperature if target_temperature is not None else "",
                            "target_steps": target_steps if target_steps is not None else "",
                            "step": current_step,
                            "li_id": atom_id,
                            "x": pos[0],
                            "y": pos[1],
                            "z": pos[2],
                            "dx": disp[0],
                            "dy": disp[1],
                            "dz": disp[2],
                            "dr2": float(np.dot(disp, disp)),
                            "dxy2": float(disp[0] ** 2 + disp[1] ** 2),
                        }
                    )
            i += 1 + int(current_atoms or 0)
            continue
        i += 1
    return rows


def expected_steps_for_group(target_steps: object, default_expected_steps: int) -> int:
    if target_steps not in ("", None):
        try:
            return int(float(target_steps))
        except (TypeError, ValueError):
            pass
    return default_expected_steps


def summarize_md(thermo_rows: list[dict[str, object]], perf_by_case: dict[tuple[str, object, object], dict[str, object]], expected_steps: int) -> list[dict[str, object]]:
    by_case: dict[tuple[str, object, object], list[dict[str, object]]] = defaultdict(list)
    for row in thermo_rows:
        by_case[(str(row["case"]), row.get("target_temperature_k", ""), row.get("target_steps", ""))].append(row)
    summaries = []
    for (case, target_temperature, target_steps), rows in sorted(by_case.items()):
        rows = sorted(rows, key=lambda row: int(row["step"]))
        first = rows[0]
        last = rows[-1]
        temps = np.asarray([float(row["temperature_k"]) for row in rows], dtype=float)
        etotal = np.asarray([float(row["total_energy_ev"]) for row in rows], dtype=float)
        expected_for_this_run = expected_steps_for_group(target_steps, expected_steps)
        summary = {
            "case": case,
            "target_temperature_k": target_temperature,
            "target_steps": target_steps,
            "n_thermo_rows": len(rows),
            "first_step": int(first["step"]),
            "last_step": int(last["step"]),
            "expected_steps": expected_for_this_run,
            "completed_expected_steps": int(last["step"]) >= expected_for_this_run,
            "mean_temperature_k": float(np.mean(temps)),
            "std_temperature_k": float(np.std(temps)),
            "total_energy_drift_ev": float(etotal[-1] - etotal[0]),
            "total_energy_drift_ev_atom_assuming_last_natoms": "",
        }
        perf = perf_by_case.get((case, target_temperature, target_steps), {})
        if not perf:
            for (perf_case, perf_temperature, _perf_steps), perf_value in perf_by_case.items():
                if perf_case == case and perf_temperature == target_temperature:
                    perf = perf_value
                    break
        summary.update(perf)
        if summary.get("natoms"):
            summary["total_energy_drift_ev_atom_assuming_last_natoms"] = float(summary["total_energy_drift_ev"]) / int(summary["natoms"])
        summaries.append(summary)
    return summaries


def aggregate_li_msd(li_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, object, object, int], list[dict[str, object]]] = defaultdict(list)
    for row in li_rows:
        grouped[(str(row["case"]), row.get("target_temperature_k", ""), row.get("target_steps", ""), int(row["step"]))].append(row)
    rows = []
    for (case, target_temperature, target_steps, step), items in sorted(grouped.items()):
        rows.append(
            {
                "case": case,
                "target_temperature_k": target_temperature,
                "target_steps": target_steps,
                "step": step,
                "time_ps": step * 0.001,
                "n_li": len(items),
                "li_msd_total_a2": float(np.mean([float(item["dr2"]) for item in items])),
                "li_msd_xy_a2": float(np.mean([float(item["dxy2"]) for item in items])),
                "li_mean_abs_dz_a": float(np.mean([abs(float(item["dz"])) for item in items])),
            }
        )
    return rows


def make_plots(output_dir: Path, thermo_rows: list[dict[str, object]], li_msd_rows: list[dict[str, object]]) -> None:
    if not plt:
        return
    by_case: dict[tuple[str, object], list[dict[str, object]]] = defaultdict(list)
    for row in thermo_rows:
        by_case[(str(row["case"]), row.get("target_temperature_k", ""))].append(row)
    if by_case:
        fig, axes = plt.subplots(2, 1, figsize=(8.0, 6.0), sharex=True)
        for (case, target_temperature), rows in sorted(by_case.items()):
            rows = sorted(rows, key=lambda row: int(row["step"]))
            label = f"{case} {target_temperature}K"
            axes[0].plot([float(row["time_ps"]) for row in rows], [float(row["temperature_k"]) for row in rows], label=label)
            e0 = float(rows[0]["total_energy_ev"])
            axes[1].plot([float(row["time_ps"]) for row in rows], [float(row["total_energy_ev"]) - e0 for row in rows], label=label)
        axes[0].set_ylabel("Temperature (K)")
        axes[0].set_title("Short MLMD stability")
        axes[1].set_xlabel("Time (ps)")
        axes[1].set_ylabel("Total energy drift (eV)")
        axes[0].legend(fontsize=7, ncol=2)
        fig.tight_layout()
        fig.savefig(output_dir / "md_temperature_energy.png", dpi=220)
        plt.close(fig)

    by_case_msd: dict[tuple[str, object], list[dict[str, object]]] = defaultdict(list)
    for row in li_msd_rows:
        by_case_msd[(str(row["case"]), row.get("target_temperature_k", ""))].append(row)
    if by_case_msd:
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        for (case, target_temperature), rows in sorted(by_case_msd.items()):
            rows = sorted(rows, key=lambda row: int(row["step"]))
            ax.plot([float(row["time_ps"]) for row in rows], [float(row["li_msd_xy_a2"]) for row in rows], label=f"{case} {target_temperature}K")
        ax.set_xlabel("Time (ps)")
        ax.set_ylabel("Li xy MSD (A^2)")
        ax.set_title("Short-run Li in-plane displacement")
        ax.legend(fontsize=7, ncol=2)
        fig.tight_layout()
        fig.savefig(output_dir / "md_li_xy_msd.png", dpi=220)
        plt.close(fig)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    include_cases = split_cases(args.include_cases)
    exclude_cases = split_cases(args.exclude_cases)

    thermo_rows: list[dict[str, object]] = []
    perf_by_case: dict[tuple[str, object, object], dict[str, object]] = {}
    for log_path in expand_globs(Path(args.log_dir), args.log_glob):
        case, target_temperature, target_steps = meta_from_path(log_path)
        if not keep_case(case, include_cases, exclude_cases):
            continue
        rows, perf = parse_thermo(log_path)
        thermo_rows.extend(rows)
        perf_by_case[(case, target_temperature if target_temperature is not None else "", target_steps if target_steps is not None else "")] = perf

    li_rows: list[dict[str, object]] = []
    for traj_path in expand_globs(Path(args.traj_dir), args.traj_glob):
        case = case_from_path(traj_path)
        if not keep_case(case, include_cases, exclude_cases):
            continue
        li_rows.extend(parse_lammpstrj(traj_path))
    thermo_rows = filter_rows(thermo_rows, include_cases, exclude_cases, args.max_step)
    li_rows = filter_rows(li_rows, include_cases, exclude_cases, args.max_step)
    li_msd_rows = aggregate_li_msd(li_rows)
    summaries = summarize_md(thermo_rows, perf_by_case, args.expected_steps)

    write_csv(output_dir / "md_thermo.csv", thermo_rows)
    write_csv(output_dir / "md_li_displacements.csv", li_rows)
    write_csv(output_dir / "md_li_msd.csv", li_msd_rows)
    write_csv(output_dir / "md_summary.csv", summaries)
    (output_dir / "md_summary.json").write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    make_plots(output_dir, thermo_rows, li_msd_rows)

    completed = sum(1 for row in summaries if row.get("completed_expected_steps"))
    print(f"Parsed {len(summaries)} MD logs; {completed}/{len(summaries)} reached expected steps.")
    print(f"Wrote MD analysis to {output_dir}")
    return 0 if summaries else 1


if __name__ == "__main__":
    raise SystemExit(main())
