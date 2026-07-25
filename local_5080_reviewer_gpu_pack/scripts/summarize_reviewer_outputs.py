#!/usr/bin/env python3
"""Summarize reviewer GPU outputs into one manifest."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def count_csv(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in csv.DictReader(handle)))


def main() -> int:
    root = Path.cwd()
    eval_dir = root / "results/review_revision/mace_eval"
    md_log_dir = root / "review_revision/md_logs"
    committee_models = sorted((root / "models/review_revision").glob("*.model"))
    manifest = {
        "mace_eval": {
            "summary_files": sorted(str(p) for p in eval_dir.glob("*_summary.csv")),
            "parity_files": sorted(str(p) for p in eval_dir.glob("*_parity.csv")),
            "summary_rows": {p.name: count_csv(p) for p in eval_dir.glob("*_summary.csv")},
            "parity_rows": {p.name: count_csv(p) for p in eval_dir.glob("*_parity.csv")},
        },
        "committee": {
            "model_files": [str(p) for p in committee_models],
            "n_models": len(committee_models),
        },
        "md": {
            "log_files": sorted(str(p) for p in md_log_dir.glob("*.log")),
            "msd_files": sorted(str(p) for p in (root / "review_revision/md_outputs").glob("*.li_msd.dat")),
            "trajectory_files": sorted(str(p) for p in (root / "trajectories/review_revision").glob("*.lammpstrj")),
        },
    }
    out = root / "results/review_revision/reviewer_gpu_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
