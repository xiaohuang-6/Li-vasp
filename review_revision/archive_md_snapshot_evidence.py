#!/usr/bin/env python3
"""Archive traceability evidence for MD-snapshot VASP single-point checks."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

import numpy as np
from ase.io import read


OUTCAR_ENERGY_RE = re.compile(r"energy\s+without entropy\s*=\s*([-+0-9.]+)")
FATAL_RE = re.compile(
    r"ERROR|Error|VERY BAD NEWS|segmentation|SIGSEGV|KILLED|killed|ZBRENT|Sub-Space-Matrix is not hermitian"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="review_revision/high_displacement_converged_jobs/combined_manifest.csv",
    )
    parser.add_argument("--output-prefix", default="review_revision/SNAPSHOT_DFT_EVIDENCE")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys or ["status"])
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_meta(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "size_bytes": "", "mtime_iso": "", "sha256": ""}
    stat = path.stat()
    return {
        "exists": True,
        "size_bytes": stat.st_size,
        "mtime_iso": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "sha256": sha256(path),
    }


def last_energy_from_outcar(path: Path) -> float | str:
    if not path.exists():
        return ""
    matches = OUTCAR_ENERGY_RE.findall(path.read_text(errors="replace"))
    return float(matches[-1]) if matches else ""


def read_forces_status(path: Path) -> tuple[bool, float | str, str]:
    try:
        atoms = read(path, index=-1, format="vasp-out")
        forces = np.asarray(atoms.get_forces(), dtype=float)
        return True, float(np.sqrt(np.mean((forces.reshape(-1) * 1000.0) ** 2))), ""
    except Exception as exc:  # noqa: BLE001
        return False, "", str(exc)


def final_scf_state(job_dir: Path, outcar_text: str) -> tuple[bool, int, int]:
    oszicar = job_dir / "OSZICAR"
    oszicar_text = oszicar.read_text(errors="replace") if oszicar.exists() else ""
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
        outcar_text = outcar.read_text(errors="replace") if outcar.exists() else ""
        log_text = vasp_log.read_text(errors="replace") if vasp_log.exists() else ""
        forces_readable, dft_force_rms, force_error = read_forces_status(outcar)
        electronic_converged, final_scf_iteration, nelm = final_scf_state(
            job_dir, outcar_text
        )
        outcar_meta = file_meta(outcar)
        oszicar_meta = file_meta(oszicar)
        log_meta = file_meta(vasp_log)
        rows.append(
            {
                "case": item.get("case", ""),
                "seed": item.get("seed", ""),
                "step": item.get("step", ""),
                "time_ps": item.get("time_ps", ""),
                "msd_xy_a2": item.get("msd_xy_a2", ""),
                "scf_provenance": item.get("scf_provenance", ""),
                "job_dir": str(job_dir),
                "outcar_exists": outcar_meta["exists"],
                "outcar_size_bytes": outcar_meta["size_bytes"],
                "outcar_mtime_iso": outcar_meta["mtime_iso"],
                "outcar_sha256": outcar_meta["sha256"],
                "oszicar_sha256": oszicar_meta["sha256"],
                "vasp_log_sha256": log_meta["sha256"],
                "completed": "General timing and accounting informations for this job" in outcar_text
                or "Voluntary context switches" in log_text,
                "electronic_converged_marker": electronic_converged,
                "final_scf_iteration": final_scf_iteration,
                "nelm": nelm,
                "fatal_error": bool(FATAL_RE.search(outcar_text + "\n" + log_text)),
                "dft_energy_without_entropy_ev": last_energy_from_outcar(outcar),
                "forces_readable": forces_readable,
                "dft_force_rms_mev_a": dft_force_rms,
                "force_read_error": force_error,
            }
        )
    return rows


def write_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    completed = sum(bool(row["completed"]) for row in rows)
    converged = sum(bool(row["electronic_converged_marker"]) for row in rows)
    fatal = sum(bool(row["fatal_error"]) for row in rows)
    force_ok = sum(bool(row["forces_readable"]) for row in rows)
    lines = [
        "# Snapshot DFT Evidence Archive",
        "",
        f"This file records traceability evidence for {len(rows)} high-displacement MD",
        "snapshot VASP single-point checks used in the manuscript. Energies and",
        "convergence status are read from the current OUTCAR files; SHA256 hashes",
        "allow each number to be traced back to a specific file state.",
        "",
        f"- Snapshot rows: {len(rows)}.",
        f"- Completed OUTCAR/log markers: {completed}/{len(rows)}.",
        f"- Electronic convergence markers: {converged}/{len(rows)}.",
        f"- Fatal markers: {fatal}/{len(rows)}.",
        f"- OUTCAR forces readable by ASE: {force_ok}/{len(rows)}.",
        "",
        "| Snapshot | completed | electronic conv. | fatal | E_DFT (eV) | OUTCAR sha256 |",
        "|---|---|---|---|---:|---|",
    ]
    for row in rows:
        name = f"{row['case']}_seed{row['seed']}_step{row['step']}"
        energy = row["dft_energy_without_entropy_ev"]
        energy_text = f"{float(energy):.6f}" if energy != "" else ""
        lines.append(
            f"| {name} | {row['completed']} | {row['electronic_converged_marker']} | "
            f"{row['fatal_error']} | {energy_text} | `{row['outcar_sha256']}` |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    prefix = Path(args.output_prefix)
    rows = collect(Path(args.manifest))
    write_csv(prefix.with_suffix(".csv"), rows)
    write_markdown(prefix.with_suffix(".md"), rows)
    print(prefix.with_suffix(".md"))
    strict = len(rows) == 9 and all(
        row["completed"]
        and row["electronic_converged_marker"]
        and int(row["final_scf_iteration"]) < int(row["nelm"])
        and not row["fatal_error"]
        and row["dft_energy_without_entropy_ev"] != ""
        and row["forces_readable"]
        for row in rows
    )
    return 0 if strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
