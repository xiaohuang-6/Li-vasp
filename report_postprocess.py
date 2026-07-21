#!/usr/bin/env python3
"""Regenerate lightweight report tables and diagnostics from local run outputs.

The script intentionally writes only generated artifacts under ``results/``.
It does not require those artifacts to be tracked in Git.
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
    from ase.io import read
except Exception:  # noqa: BLE001
    read = None

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # noqa: BLE001
    plt = None


FAMILIES = ("A_Perfect", "B1_Monovacancy", "B2_Divacancy", "C_StoneWales", "D_SiGraphene")
THERMO_RE = re.compile(
    r"^\s*(?P<step>\d+)\s+(?P<time>[-+0-9.eE]+)\s+(?P<temp>[-+0-9.eE]+)\s+"
    r"(?P<pe>[-+0-9.eE]+)\s+(?P<ke>[-+0-9.eE]+)\s+(?P<etotal>[-+0-9.eE]+)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--sp-root", default="dft_sp_outputs")
    parser.add_argument("--dataset-report", default="data/mace_datasets/li_mace_dataset_report.json")
    parser.add_argument("--md-log-dir", default="lammps_logs/two_day_md")
    parser.add_argument("--output-dir", default="results/report")
    return parser.parse_args()


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
        for row in rows:
            writer.writerow(row)


def family_from_name(name: str) -> str:
    stripped = re.sub(r"^SP_", "", name)
    for family in FAMILIES:
        if stripped == family or stripped.startswith(f"{family}_"):
            return family
    return stripped.split("_")[0]


def label_from_name(name: str, family: str) -> str:
    stripped = re.sub(r"^SP_", "", name)
    prefix = f"{family}_"
    return stripped[len(prefix) :] if stripped.startswith(prefix) else stripped


def parse_path_label(label: str) -> tuple[str, str, int | None]:
    match = re.match(r"(path\d+)_(.+)_img(\d+)$", label)
    if not match:
        return "", "", None
    return match.group(1), match.group(2), int(match.group(3))


def collect_sp_rows(sp_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if read is None or not sp_root.exists():
        return rows
    for outcar in sorted(sp_root.glob("*/OUTCAR")):
        name = outcar.parent.name
        family = family_from_name(name)
        label = label_from_name(name, family)
        path_id, path_body, image = parse_path_label(label)
        try:
            atoms = read(outcar, index=-1, format="vasp-out")
            energy = float(atoms.get_potential_energy())
            natoms = len(atoms)
        except Exception as exc:  # noqa: BLE001
            rows.append({"config": name, "family": family, "label": label, "parse_error": str(exc)})
            continue
        rows.append(
            {
                "config": name,
                "family": family,
                "label": label,
                "kind": "path" if path_id else "site",
                "path_id": path_id,
                "path_body": path_body,
                "image": image if image is not None else "",
                "energy_ev": energy,
                "natoms": natoms,
                "energy_ev_atom": energy / natoms,
            }
        )
    return rows


def dataset_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "unreadable", "path": str(path)}
    data["status"] = "available"
    return data


def site_rankings(sp_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = [row for row in sp_rows if row.get("kind") == "site" and "energy_ev" in row]
    minima: dict[str, float] = {}
    for row in rows:
        family = str(row["family"])
        minima[family] = min(minima.get(family, math.inf), float(row["energy_ev"]))
    for row in rows:
        row["rel_to_site_min_ev"] = float(row["energy_ev"]) - minima[str(row["family"])]
    return sorted(rows, key=lambda row: (str(row["family"]), float(row["rel_to_site_min_ev"])))


def path_profiles(sp_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    path_rows = [row for row in sp_rows if row.get("kind") == "path" and "energy_ev" in row]
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in path_rows:
        grouped[(str(row["family"]), str(row["path_id"]))].append(row)

    profiles: list[dict[str, object]] = []
    barriers: list[dict[str, object]] = []
    for (family, path_id), rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row["image"]))
        energies = [float(row["energy_ev"]) for row in rows]
        emin = min(energies)
        for row in rows:
            profiles.append(
                {
                    "family": family,
                    "path_id": path_id,
                    "image": row["image"],
                    "label": row["label"],
                    "energy_ev": row["energy_ev"],
                    "rel_to_path_min_ev": float(row["energy_ev"]) - emin,
                }
            )
        barriers.append(
            {
                "family": family,
                "path_id": path_id,
                "path_label": rows[0].get("path_body", ""),
                "n_images": len(rows),
                "barrier_from_path_min_ev": max(energies) - emin,
                "delta_e_end_minus_start_ev": energies[-1] - energies[0],
            }
        )
    return profiles, barriers


def parse_md_logs(log_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for log in sorted(log_dir.glob("*.log")):
        thermo = []
        for line in log.read_text(errors="replace").splitlines():
            match = THERMO_RE.match(line)
            if match:
                thermo.append({key: float(value) for key, value in match.groupdict().items()})
        if not thermo:
            continue
        temps = np.array([row["temp"] for row in thermo], dtype=float)
        etot = np.array([row["etotal"] for row in thermo], dtype=float)
        rows.append(
            {
                "log": str(log),
                "last_step": int(thermo[-1]["step"]),
                "mean_temperature_k": float(np.mean(temps)),
                "std_temperature_k": float(np.std(temps)),
                "energy_drift_ev": float(etot[-1] - etot[0]),
            }
        )
    return rows


def plot_sites(rows: list[dict[str, object]], path: Path) -> None:
    if plt is None or not rows:
        return
    labels = [f"{row['family']}\n{row['label']}" for row in rows]
    values = [float(row["rel_to_site_min_ev"]) for row in rows]
    fig, ax = plt.subplots(figsize=(max(8, 0.45 * len(rows)), 4))
    ax.bar(range(len(rows)), values)
    ax.set_ylabel("Relative energy (eV)")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=75, ha="right", fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_paths(rows: list[dict[str, object]], path: Path) -> None:
    if plt is None or not rows:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["family"]), str(row["path_id"]))].append(row)
    for (family, path_id), items in sorted(grouped.items()):
        items = sorted(items, key=lambda row: int(row["image"]))
        ax.plot(
            [int(row["image"]) for row in items],
            [float(row["rel_to_path_min_ev"]) for row in items],
            marker="o",
            label=f"{family} {path_id}",
        )
    ax.set_xlabel("Path image")
    ax.set_ylabel("Relative energy (eV)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def write_summary(output_dir: Path, dataset: dict[str, object], sites, barriers, md_rows) -> None:
    lines = [
        "# Report Reproduction Summary",
        "",
        "This summary was generated from local outputs by `report_postprocess.py`.",
        "",
        "## Dataset",
        "",
        f"- Dataset report status: {dataset.get('status', 'unknown')}",
        f"- Dataset report path: `{dataset.get('path', 'data/mace_datasets/li_mace_dataset_report.json')}`",
        "",
        "## Li Site Screening",
        "",
        f"- Parsed site rows: {len(sites)}",
        f"- Parsed path barriers: {len(barriers)}",
        "",
        "## MD Diagnostics",
        "",
        f"- Parsed MD logs: {len(md_rows)}",
        "",
        "## Claim Boundary",
        "",
        "Fixed-geometry path spans are screening diagnostics, not CI-NEB barriers. "
        "Short MD logs are stability diagnostics, not converged diffusion coefficients.",
    ]
    (output_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output_dir / "REPORT_RESULTS_BRIEF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve()
    output_dir = (root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = dataset_summary(root / args.dataset_report)
    sp_rows = collect_sp_rows(root / args.sp_root)
    sites = site_rankings(sp_rows)
    profiles, barriers = path_profiles(sp_rows)
    md_rows = parse_md_logs(root / args.md_log_dir)

    (output_dir / "dataset_summary.json").write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    write_csv(output_dir / "site_energy_rankings.csv", sites)
    write_csv(output_dir / "path_profiles.csv", profiles)
    write_csv(output_dir / "path_barriers.csv", barriers)
    write_csv(output_dir / "md_summary.csv", md_rows)
    plot_sites(sites, output_dir / "site_energy_rankings.png")
    plot_paths(profiles, output_dir / "path_profiles.png")
    write_summary(output_dir, dataset, sites, barriers, md_rows)

    manifest = {
        "output_dir": str(output_dir),
        "files": sorted(path.name for path in output_dir.iterdir() if path.is_file()),
        "counts": {
            "sp_rows": len(sp_rows),
            "site_rows": len(sites),
            "path_profile_rows": len(profiles),
            "path_barriers": len(barriers),
            "md_logs": len(md_rows),
        },
    }
    (output_dir / "RESULTS_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote report artifacts to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
