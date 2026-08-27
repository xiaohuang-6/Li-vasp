#!/usr/bin/env python3
"""Audit final SCF iterations for all 273 DFT training-label frames."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path


FATAL_MARKERS = (
    "VERY BAD NEWS",
    "BRMIX: very serious problems",
    "ZBRENT: fatal error",
    "internal error in subroutine PRICEL",
    "Error EDDDAV",
    "Call to ZHEGV failed",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def electronic_blocks(oszicar_text: str) -> list[int]:
    blocks: list[int] = []
    final_iteration = 0
    for line in oszicar_text.splitlines():
        match = re.match(
            r"\s*(?:DAV|RMM|SDA|CGA|CG|DMP|DIA|EIG)\s*:\s*(\d+)", line
        )
        if match:
            final_iteration = int(match.group(1))
        elif re.match(r"\s*\d+\s+F=", line):
            blocks.append(final_iteration)
            final_iteration = 0
    return blocks


def audit_job(job_dir: Path, source_kind: str) -> list[dict[str, object]]:
    outcar = job_dir / "OUTCAR"
    oszicar = job_dir / "OSZICAR"
    outcar_text = outcar.read_text(encoding="utf-8", errors="replace")
    oszicar_text = oszicar.read_text(encoding="utf-8", errors="replace")
    nelm_matches = re.findall(r"\bNELM\s*=\s*(\d+)", outcar_text)
    if not nelm_matches:
        raise ValueError(f"No NELM value in {outcar}")
    nelm = int(nelm_matches[-1])
    blocks = electronic_blocks(oszicar_text)
    if not blocks:
        raise ValueError(f"No completed ionic/single-point blocks in {oszicar}")
    completed = "General timing and accounting informations for this job" in outcar_text
    fatal = any(marker in outcar_text for marker in FATAL_MARKERS)
    digest = sha256(outcar)
    return [
        {
            "source_kind": source_kind,
            "job": job_dir.name,
            "frame_index": index,
            "final_scf_iteration": final_iteration,
            "nelm": nelm,
            "completed": completed,
            "fatal": fatal,
            "strictly_converged": (
                completed and not fatal and 0 < final_iteration < nelm
            ),
            "outcar_sha256": digest,
        }
        for index, final_iteration in enumerate(blocks)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/review_revision/training_label_scf_audit.csv"),
    )
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    for directory, source_kind in (
        (args.root / "dft_outputs", "ionic_relaxation"),
        (args.root / "dft_sp_outputs", "fixed_geometry_single_point"),
    ):
        for outcar in sorted(directory.rglob("OUTCAR")):
            rows.extend(audit_job(outcar.parent, source_kind))

    counts = {
        kind: sum(row["source_kind"] == kind for row in rows)
        for kind in {str(row["source_kind"]) for row in rows}
    }
    expected = {
        "ionic_relaxation": 194,
        "fixed_geometry_single_point": 79,
    }
    if len(rows) != 273 or counts != expected:
        raise ValueError(f"Expected 273 training labels with counts {expected}; found {counts}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    usable = sum(bool(row["strictly_converged"]) for row in rows)
    print(f"Strictly converged training labels: {usable}/{len(rows)}")
    return 0 if usable == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
