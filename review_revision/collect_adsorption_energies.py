#!/usr/bin/env python3
"""Collect VASP adsorption-energy single-point results."""

from __future__ import annotations

import argparse
import csv
import math
import re
import time
from pathlib import Path


OUTCAR_ENERGY_RE = re.compile(r"energy\s+without entropy\s*=\s*([-+0-9.]+)")
OSZICAR_ENERGY_RE = re.compile(r"\bF=\s*([-+0-9.Ee+-]+)")
FATAL_RE = re.compile(
    r"ERROR|Error|VERY BAD NEWS|segmentation|SIGSEGV|KILLED|killed|ZBRENT|Sub-Space-Matrix is not hermitian"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="review_revision/adsorption_energy_jobs/adsorption_manifest.csv")
    parser.add_argument("--output-dir", default="results/review_revision/adsorption_energy_analysis")
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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def all_match_floats(pattern: re.Pattern[str], path: Path) -> list[float]:
    text = read_text(path)
    return [float(match.replace("D", "E")) for match in pattern.findall(text)]


def file_age_seconds(path: Path) -> float | str:
    if not path.exists():
        return ""
    return time.time() - path.stat().st_mtime


def collect_job_rows(manifest: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in read_csv(manifest):
        job_dir = Path(item["job_dir"])
        outcar = job_dir / "OUTCAR"
        oszicar = job_dir / "OSZICAR"
        log = job_dir / "vasp.log"
        outcar_text = read_text(outcar)
        log_text = read_text(log)
        energies = all_match_floats(OUTCAR_ENERGY_RE, outcar)
        latest = energies[-1] if energies else None
        source = "OUTCAR"
        if latest is None:
            osz_energies = all_match_floats(OSZICAR_ENERGY_RE, oszicar)
            latest = osz_energies[-1] if osz_energies else None
            source = "OSZICAR" if latest is not None else "missing"
        completed = "General timing and accounting informations for this job" in outcar_text or "Voluntary context switches" in log_text
        electronic_converged = "aborting loop because EDIFF is reached" in outcar_text
        fatal = bool(FATAL_RE.search(outcar_text + "\n" + log_text))
        usable = latest if completed and electronic_converged and not fatal else None
        rows.append(
            {
                **item,
                "outcar_exists": outcar.exists(),
                "oszicar_exists": oszicar.exists(),
                "vasp_log_exists": log.exists(),
                "outcar_age_s": file_age_seconds(outcar),
                "vasp_log_age_s": file_age_seconds(log),
                "completed": completed,
                "electronic_converged_marker": electronic_converged,
                "fatal_error": fatal,
                "scf_energy_count": len(energies),
                "latest_scf_energy_ev": latest if latest is not None else "",
                "usable_energy_ev": usable if usable is not None else "",
                "energy_source": source,
            }
        )
    return rows


def calculate_adsorption(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_component: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        by_component[(str(row["family"]), str(row["component"]))] = row
    li_ref = by_component.get(("Li_atom", "li_atom"))
    results: list[dict[str, object]] = []
    if not li_ref or li_ref.get("usable_energy_ev") == "":
        return results
    e_li = float(li_ref["usable_energy_ev"])
    families = sorted({str(row["family"]) for row in rows if row["family"] != "Li_atom"})
    for family in families:
        ads = by_component.get((family, "adsorbed"))
        sub = by_component.get((family, "substrate"))
        if not ads or not sub:
            continue
        usable = ads.get("usable_energy_ev") != "" and sub.get("usable_energy_ev") != ""
        n_li = int(float(str(ads.get("n_li", "1"))))
        e_ads = float("nan")
        if usable:
            e_ads = float(ads["usable_energy_ev"]) - float(sub["usable_energy_ev"]) - n_li * e_li
        results.append(
            {
                "family": family,
                "n_li": n_li,
                "adsorbed_energy_ev": ads.get("usable_energy_ev", ""),
                "substrate_energy_ev": sub.get("usable_energy_ev", ""),
                "li_atom_energy_ev": e_li,
                "adsorption_energy_ev_per_li": e_ads / n_li if usable else "",
                "usable": usable,
            }
        )
    return results


def fmt(value: object, digits: int = 6) -> str:
    if value == "" or value is None:
        return ""
    try:
        numeric = float(value)
    except Exception:  # noqa: BLE001
        return str(value)
    if math.isnan(numeric):
        return ""
    return f"{numeric:.{digits}f}"


def write_markdown(output_dir: Path, job_rows: list[dict[str, object]], eads_rows: list[dict[str, object]]) -> None:
    completed = sum(bool(row["completed"]) for row in job_rows)
    usable = sum(row["usable_energy_ev"] != "" for row in job_rows)
    fatal = sum(bool(row["fatal_error"]) for row in job_rows)
    lines = [
        "# D3/Dipole Adsorption Energy Status",
        "",
        f"- Completed jobs: {completed}/{len(job_rows)}.",
        f"- Usable converged energies: {usable}/{len(job_rows)}.",
        f"- Jobs with fatal markers: {fatal}/{len(job_rows)}.",
        "",
        "Adsorption energies use E_ads = E(Li+substrate) - E(substrate) - n_Li E(Li_atom).",
        "",
        "## Adsorption Energies",
        "",
        "| Family | nLi | E_ads per Li (eV) | usable |",
        "|---|---:|---:|---|",
    ]
    for row in eads_rows:
        lines.append(
            f"| {row['family']} | {row['n_li']} | {fmt(row['adsorption_energy_ev_per_li'])} | {row['usable']} |"
        )
    lines.extend(
        [
            "",
            "## Job Energies",
            "",
            "| Job | family | component | completed | electronic conv. | fatal | usable energy (eV) |",
            "|---|---|---|---|---|---|---:|",
        ]
    )
    for row in job_rows:
        lines.append(
            "| {job} | {family} | {component} | {completed} | {conv} | {fatal} | {energy} |".format(
                job=Path(str(row["job_dir"])).name,
                family=row["family"],
                component=row["component"],
                completed=row["completed"],
                conv=row["electronic_converged_marker"],
                fatal=row["fatal_error"],
                energy=fmt(row["usable_energy_ev"]),
            )
        )
    (output_dir / "ADSORPTION_ENERGY_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    job_rows = collect_job_rows(Path(args.manifest))
    eads_rows = calculate_adsorption(job_rows)
    write_csv(output_dir / "adsorption_job_status.csv", job_rows)
    write_csv(output_dir / "adsorption_energies.csv", eads_rows)
    write_markdown(output_dir, job_rows, eads_rows)
    print(output_dir / "ADSORPTION_ENERGY_STATUS.md")
    return 0 if job_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
