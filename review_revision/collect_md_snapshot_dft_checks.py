#!/usr/bin/env python3
"""Collect VASP single-point results for selected MD snapshot DFT checks."""

from __future__ import annotations

import argparse
import csv
import math
import re
import time
from pathlib import Path


OUTCAR_ENERGY_RE = re.compile(r"energy\s+without entropy\s*=\s*([-+0-9.]+)")
OSZICAR_ENERGY_RE = re.compile(r"\bF=\s*([-+0-9.Ee]+)")
FATAL_RE = re.compile(
    r"ERROR|Error|VERY BAD NEWS|segmentation|SIGSEGV|KILLED|killed|ZBRENT|Sub-Space-Matrix is not hermitian"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="review_revision/md_snapshot_dft_jobs/md_snapshot_dft_manifest.csv")
    parser.add_argument("--output-dir", default="results/review_revision/md_snapshot_dft_analysis")
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


def all_match_floats(pattern: re.Pattern[str], path: Path) -> list[float]:
    if not path.exists():
        return []
    matches = pattern.findall(path.read_text(errors="replace"))
    if not matches:
        return []
    return [float(match.replace("D", "E")) for match in matches]


def last_match_float(pattern: re.Pattern[str], path: Path) -> float | None:
    matches = all_match_floats(pattern, path)
    return matches[-1] if matches else None


def file_age_seconds(path: Path) -> float | str:
    if not path.exists():
        return ""
    return time.time() - path.stat().st_mtime


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def final_scf_state(job_dir: Path, outcar_text: str) -> tuple[bool, int, int]:
    oszicar_text = read_text_if_exists(job_dir / "OSZICAR")
    iterations = [
        int(value)
        for value in re.findall(
            r"^\s*(?:DAV|RMM|SDA|CGA|CG|DMP|DIA|EIG)\s*:\s*(\d+)",
            oszicar_text,
            re.MULTILINE,
        )
    ]
    nelm_matches = re.findall(r"\bNELM\s*=\s*(\d+)", outcar_text)
    final_iteration = iterations[-1] if iterations else 0
    nelm = int(nelm_matches[-1]) if nelm_matches else 0
    converged = (
        "aborting loop because EDIFF is reached" in outcar_text
        and final_iteration > 0
        and nelm > 0
        and final_iteration < nelm
    )
    return converged, final_iteration, nelm


def collect(manifest: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in read_csv(manifest):
        job_dir = Path(item["job_dir"])
        outcar = job_dir / "OUTCAR"
        oszicar = job_dir / "OSZICAR"
        vasp_log = job_dir / "vasp.log"
        outcar_text = read_text_if_exists(outcar)
        log_text = read_text_if_exists(vasp_log)
        outcar_energies = all_match_floats(OUTCAR_ENERGY_RE, outcar)
        latest_energy = outcar_energies[-1] if outcar_energies else None
        source = "OUTCAR"
        if latest_energy is None:
            latest_energy = last_match_float(OSZICAR_ENERGY_RE, oszicar)
            source = "OSZICAR" if latest_energy is not None else "missing"
        completed = "General timing and accounting informations for this job" in outcar_text or "Voluntary context switches" in log_text
        electronic_converged, final_scf_iteration, nelm = final_scf_state(
            job_dir, outcar_text
        )
        usable_energy = latest_energy if completed and electronic_converged else None
        rows.append(
            {
                **item,
                "outcar_exists": outcar.exists(),
                "oszicar_exists": oszicar.exists(),
                "vasp_log_exists": vasp_log.exists(),
                "outcar_age_s": file_age_seconds(outcar),
                "vasp_log_age_s": file_age_seconds(vasp_log),
                "completed": completed,
                "electronic_converged_marker": electronic_converged,
                "final_scf_iteration": final_scf_iteration,
                "nelm": nelm,
                "fatal_error": bool(FATAL_RE.search(outcar_text + "\n" + log_text)),
                "scf_energy_count": len(outcar_energies),
                "latest_scf_energy_ev": latest_energy if latest_energy is not None else "",
                "usable_dft_energy_ev": usable_energy if usable_energy is not None else "",
                "energy_source": source if latest_energy is not None else "missing",
            }
        )
    return rows


def write_markdown(output_dir: Path, rows: list[dict[str, object]]) -> None:
    completed = sum(bool(row["completed"]) for row in rows)
    fatal = sum(bool(row["fatal_error"]) for row in rows)
    usable_energies = [float(row["usable_dft_energy_ev"]) for row in rows if row["usable_dft_energy_ev"] != ""]
    latest_energies = [float(row["latest_scf_energy_ev"]) for row in rows if row["latest_scf_energy_ev"] != ""]
    lines = [
        "# MD Snapshot DFT Check Status",
        "",
        f"- Completed snapshot checks: {completed}/{len(rows)}.",
        f"- Snapshot checks with fatal error markers: {fatal}/{len(rows)}.",
        f"- Snapshot checks with usable converged energies: {len(usable_energies)}/{len(rows)}.",
        f"- Snapshot checks with any in-progress SCF energy: {len(latest_energies)}/{len(rows)}.",
        "",
        "| Job | case | seed | step | MSDxy (A^2) | completed | electronic conv. | fatal | latest SCF energy (eV) | usable energy (eV) |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        latest = row["latest_scf_energy_ev"]
        usable = row["usable_dft_energy_ev"]
        lines.append(
            "| {job} | {case} | {seed} | {step} | {msd_xy} | {completed} | {electronic} | {fatal} | {latest} | {usable} |".format(
                job=Path(str(row["job_dir"])).name,
                case=row["case"],
                seed=row["seed"],
                step=row["step"],
                msd_xy=f"{float(row['msd_xy_a2']):.1f}",
                completed=row["completed"],
                electronic=row["electronic_converged_marker"],
                fatal=row["fatal_error"],
                latest=f"{float(latest):.6f}" if latest != "" and not math.isnan(float(latest)) else "",
                usable=f"{float(usable):.6f}" if usable != "" and not math.isnan(float(usable)) else "",
            )
        )
    (output_dir / "MD_SNAPSHOT_DFT_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = collect(Path(args.manifest))
    write_csv(output_dir / "md_snapshot_dft_results.csv", rows)
    write_markdown(output_dir, rows)
    print(output_dir / "MD_SNAPSHOT_DFT_STATUS.md")
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
