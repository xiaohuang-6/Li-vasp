#!/usr/bin/env python3
"""Check fixed-geometry VASP single-point label jobs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from ase.io import read


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize VASP SP job status.")
    parser.add_argument("--jobs-root", default="dft_sp_outputs")
    parser.add_argument("--report", default=None)
    return parser.parse_args()


def check_job(job_dir: Path) -> dict[str, object]:
    outcar = job_dir / "OUTCAR"
    vasp_log = job_dir / "vasp.log"
    record: dict[str, object] = {
        "case": job_dir.name,
        "path": str(job_dir),
        "status": "missing_outcar",
    }
    if not outcar.exists() or outcar.stat().st_size == 0:
        return record

    text_tail = outcar.read_text(errors="replace")[-20000:]
    has_timing = "General timing" in text_tail
    record["has_general_timing"] = has_timing
    try:
        atoms = read(outcar, index=-1, format="vasp-out")
        energy = float(atoms.get_potential_energy())
        forces = np.asarray(atoms.get_forces(), dtype=float)
        record.update(
            {
                "status": "complete" if has_timing else "parsed_no_timing",
                "natoms": len(atoms),
                "energy": energy,
                "max_force": float(np.max(np.abs(forces))),
            }
        )
    except Exception as exc:  # noqa: BLE001
        record.update({"status": "parse_failed", "error": str(exc)})

    if vasp_log.exists():
        log_tail = vasp_log.read_text(errors="replace")[-4000:]
        if "error" in log_tail.lower() or "forrtl" in log_tail.lower():
            record["vasp_log_tail"] = log_tail.splitlines()[-20:]
    return record


def main() -> int:
    args = parse_args()
    root = Path(args.jobs_root)
    job_dirs = sorted(path for path in root.iterdir() if path.is_dir()) if root.exists() else []
    records = [check_job(path) for path in job_dirs]
    counts: dict[str, int] = {}
    for record in records:
        counts[str(record["status"])] = counts.get(str(record["status"]), 0) + 1

    report = {"jobs_root": str(root), "counts": counts, "records": records}
    report_path = Path(args.report) if args.report else root / "sp_job_status.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(counts, indent=2))
    print(f"Wrote {report_path}")
    return 0 if counts.get("parse_failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
