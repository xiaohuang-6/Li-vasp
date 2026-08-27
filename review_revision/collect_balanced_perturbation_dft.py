#!/usr/bin/env python3
"""Collect completion and force-readability evidence for the balanced benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path

import numpy as np
from ase.io import read


FATAL_MARKERS = (
    "VERY BAD NEWS",
    "BRMIX: very serious problems",
    "ZBRENT: fatal error",
    "internal error in subroutine PRICEL",
    "Error EDDDAV",
    "Call to ZHEGV failed",
)

EXPECTED_FAMILIES = {
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
}


def final_scf_state(job_dir: Path, outcar_text: str) -> tuple[bool, int, int]:
    oszicar = job_dir / "OSZICAR"
    oszicar_text = (
        oszicar.read_text(encoding="utf-8", errors="replace")
        if oszicar.is_file()
        else ""
    )
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(rows: list[dict[str, str]]) -> None:
    counts = {
        family: sum(row["family"] == family for row in rows)
        for family in EXPECTED_FAMILIES
    }
    if len(rows) != 25 or set(row["family"] for row in rows) != EXPECTED_FAMILIES:
        raise ValueError("Balanced benchmark must contain exactly five families and 25 rows")
    if any(count != 5 for count in counts.values()):
        raise ValueError(f"Balanced benchmark must contain five rows per family: {counts}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="review_revision/balanced_perturbation_dft_jobs/manifest.csv",
    )
    parser.add_argument(
        "--output-dir",
        default="results/review_revision/balanced_perturbation_dft_analysis",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with Path(args.manifest).open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    validate_manifest(manifest)

    rows: list[dict[str, object]] = []
    for item in manifest:
        job_dir = Path(item["job_dir"])
        outcar = job_dir / "OUTCAR"
        text = outcar.read_text(encoding="utf-8", errors="replace") if outcar.exists() else ""
        completed = "General timing and accounting informations for this job" in text
        electronic_converged, final_scf_iteration, nelm = final_scf_state(job_dir, text)
        fatal = any(marker in text for marker in FATAL_MARKERS)
        forces_readable = False
        energy_ev = float("nan")
        force_rms_ev_a = float("nan")
        error = ""
        if completed and not fatal:
            try:
                atoms = read(outcar, index=-1, format="vasp-out")
                energy_ev = float(atoms.get_potential_energy())
                forces = np.asarray(atoms.get_forces(), dtype=float)
                force_rms_ev_a = float(np.sqrt(np.mean(forces * forces)))
                forces_readable = forces.shape == (len(atoms), 3) and np.isfinite(forces).all()
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
        usable = completed and electronic_converged and not fatal and forces_readable
        rows.append(
            {
                **item,
                "outcar_exists": outcar.exists(),
                "outcar_size_bytes": outcar.stat().st_size if outcar.exists() else 0,
                "outcar_mtime_ns": outcar.stat().st_mtime_ns if outcar.exists() else 0,
                "outcar_sha256": sha256(outcar) if outcar.exists() else "",
                "completed": completed,
                "electronic_converged": electronic_converged,
                "final_scf_iteration": final_scf_iteration,
                "nelm": nelm,
                "fatal": fatal,
                "forces_readable": forces_readable,
                "usable": usable,
                "energy_ev": energy_ev,
                "dft_force_rms_ev_a": force_rms_ev_a,
                "parse_error": error,
            }
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "balanced_perturbation_dft_status.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    usable_count = sum(str(row["usable"]) == "True" for row in rows)
    lines = [
        "# Balanced Perturbation DFT Status",
        "",
        f"- Completed and usable: {usable_count}/{len(rows)}.",
        "- Benchmark membership was fixed without MACE predictions.",
        "",
        "| Family | sigma (A) | replicate | complete | SCF converged | forces readable | usable |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['family']} | {row['sigma_a']} | {row['replicate']} | "
            f"{row['completed']} | {row['electronic_converged']} | "
            f"{row['forces_readable']} | {row['usable']} |"
        )
    (output_dir / "BALANCED_PERTURBATION_DFT_STATUS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"Usable: {usable_count}/{len(rows)}")
    return 0 if usable_count == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
