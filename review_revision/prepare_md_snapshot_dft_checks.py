#!/usr/bin/env python3
"""Prepare VASP single-point checks for high-displacement MD snapshots.

The reviewer concern is that large MACE/LAMMPS displacements may be out-of-domain
MLIP artifacts. This script selects a small number of high-MSD snapshots and
creates VASP single-point jobs so those configurations can be checked directly.
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
from pathlib import Path

from ase.io import read, write


INCAR_TEMPLATE = """SYSTEM = Li graphene MD snapshot DFT check
ENCUT = 520
EDIFF = 1E-6
ISMEAR = 0
SIGMA = 0.05
PREC = Accurate
LREAL = .FALSE.
ALGO = Normal
NCORE = 4

IBRION = -1
NSW = 0
ISIF = 2

ISPIN = 2
ISYM = 0
LASPH = .TRUE.
ADDGRID = .TRUE.
LWAVE = .FALSE.
LCHARG = .FALSE.

NELM = 160
MAGMOM = {magmom}
"""


KPOINTS = """Automatic mesh
0
Gamma
1 1 1
0 0 0
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--md-runs-csv", default="results/review_revision/gpu_analysis/review_md_runs.csv")
    parser.add_argument("--trajectories-dir", default="trajectories/review_revision")
    parser.add_argument("--msd-dir", default="review_revision/md_outputs")
    parser.add_argument("--output-dir", default="review_revision/md_snapshot_dft_jobs")
    parser.add_argument("--top-runs", type=int, default=3, help="Number of MD runs to select by final MSDxy.")
    parser.add_argument("--snapshots-per-run", type=int, default=2, help="Highest-MSD snapshots per selected run.")
    parser.add_argument("--also-final", action="store_true", help="Also include the final timestep for each selected run.")
    parser.add_argument("--potcar-root", default="", help="Optional PAW_PBE root. If omitted, copy dft_outputs/<case>/POTCAR when possible.")
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys or ["status"])
        writer.writeheader()
        writer.writerows(rows)


def magmom_for_atoms(atoms) -> str:
    counts: dict[str, int] = {}
    for symbol in atoms.get_chemical_symbols():
        counts[symbol] = counts.get(symbol, 0) + 1
    parts: list[str] = []
    if counts.get("C"):
        parts.append(f"{counts['C']}*0.1")
    if counts.get("Li"):
        parts.append(f"{counts['Li']}*1.0")
    if counts.get("Si"):
        parts.append(f"{counts['Si']}*0.1")
    return " ".join(parts)


def ordered_symbols(atoms) -> list[str]:
    symbols: list[str] = []
    for symbol in atoms.get_chemical_symbols():
        if symbol not in symbols:
            symbols.append(symbol)
    return symbols


def write_potcar(job_dir: Path, atoms, case: str, potcar_root: str) -> str:
    if potcar_root:
        chunks = []
        for symbol in ordered_symbols(atoms):
            choice = "Li_sv" if symbol == "Li" else symbol
            potcar = Path(potcar_root) / choice / "POTCAR"
            if not potcar.exists():
                raise FileNotFoundError(f"Missing POTCAR for {symbol}: {potcar}")
            chunks.append(potcar.read_bytes())
        (job_dir / "POTCAR").write_bytes(b"".join(chunks))
        return f"potcar_root:{potcar_root}"

    source = Path("dft_outputs") / case / "POTCAR"
    if source.exists():
        shutil.copy2(source, job_dir / "POTCAR")
        return str(source)

    note = " ".join("Li_sv" if sym == "Li" else sym for sym in ordered_symbols(atoms))
    (job_dir / "POTCAR_REQUIRED.txt").write_text(
        "Create POTCAR using licensed PAW_PBE potentials in this order:\n" + note + "\n",
        encoding="utf-8",
    )
    return "missing"


def load_msd(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 5:
                continue
            step = int(float(fields[0]))
            msd_x = float(fields[1])
            msd_y = float(fields[2])
            msd_z = float(fields[3])
            msd_total = float(fields[4])
            rows.append(
                {
                    "step": step,
                    "msd_x": msd_x,
                    "msd_y": msd_y,
                    "msd_z": msd_z,
                    "msd_total": msd_total,
                    "msd_xy": msd_x + msd_y,
                }
            )
    return rows


def dump_timesteps(path: Path) -> list[int]:
    steps: list[int] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("ITEM: TIMESTEP"):
                step_line = next(handle)
                steps.append(int(step_line.strip()))
    return steps


def select_runs(md_runs_csv: Path, top_runs: int) -> list[dict[str, str]]:
    rows = read_csv(md_runs_csv)
    candidates = [
        row
        for row in rows
        if row.get("lost_atoms_or_error") == "False"
        and (row.get("completed_target") == "True" or row.get("completed_100ps") == "True")
    ]
    candidates.sort(key=lambda row: float(row["final_msd_xy_a2"]), reverse=True)
    return candidates[:top_runs]


def select_steps(msd_rows: list[dict[str, float]], snapshots_per_run: int, also_final: bool) -> list[int]:
    ordered = sorted(msd_rows, key=lambda row: row["msd_xy"], reverse=True)
    steps: list[int] = []
    for row in ordered:
        step = int(row["step"])
        if step not in steps:
            steps.append(step)
        if len(steps) >= snapshots_per_run:
            break
    if also_final and msd_rows:
        final_step = int(msd_rows[-1]["step"])
        if final_step not in steps:
            steps.append(final_step)
    return sorted(steps)


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    selected_runs = select_runs(Path(args.md_runs_csv), args.top_runs)
    job_dirs: list[Path] = []
    manifest_rows: list[dict[str, object]] = []

    for run in selected_runs:
        case = run["case"]
        structure_case = run.get("structure") or case
        seed = run["seed"]
        steps = run["steps"]
        run_name = f"{case}_400K_seed{seed}_{steps}steps"
        traj = Path(args.trajectories_dir) / f"{run_name}.lammpstrj"
        msd = Path(args.msd_dir) / f"{run_name}.li_msd.dat"
        if not traj.exists() or not msd.exists():
            print(f"Skipping {run_name}: missing trajectory or MSD file")
            continue
        timesteps = dump_timesteps(traj)
        timestep_to_index = {step: idx for idx, step in enumerate(timesteps)}
        msd_rows = load_msd(msd)
        used_dump_steps: set[int] = set()
        for step in select_steps(msd_rows, args.snapshots_per_run, args.also_final):
            if step not in timestep_to_index:
                if not timesteps:
                    print(f"Skipping {run_name} step {step}: no timesteps in trajectory dump")
                    continue
                dump_step = min(timesteps, key=lambda candidate: abs(candidate - step))
                print(f"Using nearest dumped timestep for {run_name}: requested {step}, using {dump_step}")
            else:
                dump_step = step
            if dump_step in used_dump_steps:
                continue
            used_dump_steps.add(dump_step)
            frame_index = timestep_to_index[dump_step]
            atoms = read(traj, index=frame_index, format="lammps-dump-text")
            atoms.wrap()
            job_dir = output_dir / f"{case}_seed{seed}_step{dump_step:06d}"
            job_dir.mkdir(parents=True)
            write(job_dir / "POSCAR", atoms, format="vasp", direct=True, sort=True)
            (job_dir / "INCAR").write_text(INCAR_TEMPLATE.format(magmom=magmom_for_atoms(atoms)), encoding="utf-8")
            (job_dir / "KPOINTS").write_text(KPOINTS, encoding="utf-8")
            potcar_source = write_potcar(job_dir, atoms, structure_case, args.potcar_root)
            msd_match = next((row for row in msd_rows if int(row["step"]) == step), {})
            job_dirs.append(job_dir)
            manifest_rows.append(
                {
                    "job_dir": str(job_dir.resolve()),
                    "case": case,
                    "structure": structure_case,
                    "seed": seed,
                    "step": dump_step,
                    "requested_step": step,
                    "time_ps": dump_step / 1000.0,
                    "trajectory": str(traj),
                    "frame_index": frame_index,
                    "msd_xy_a2": msd_match.get("msd_xy", math.nan),
                    "msd_total_a2": msd_match.get("msd_total", math.nan),
                    "potcar_source": potcar_source,
                    "natoms": len(atoms),
                }
            )

    (output_dir / "md_snapshot_dft_job_list.txt").write_text(
        "\n".join(str(path.resolve()) for path in job_dirs) + ("\n" if job_dirs else ""),
        encoding="utf-8",
    )
    write_csv(output_dir / "md_snapshot_dft_manifest.csv", manifest_rows)
    print(f"Wrote {len(job_dirs)} MD snapshot DFT check jobs")
    print(output_dir / "md_snapshot_dft_job_list.txt")
    return 0 if job_dirs else 1


if __name__ == "__main__":
    raise SystemExit(main())
