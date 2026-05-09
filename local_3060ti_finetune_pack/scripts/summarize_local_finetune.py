#!/usr/bin/env python3
"""Summarize local fine-tune outputs after copying the pack back."""

from __future__ import annotations

import json
from pathlib import Path

from ase.io import read


ROOT = Path(__file__).resolve().parents[1]


def status(path: Path) -> str:
    return "OK" if path.exists() and path.stat().st_size > 0 else "MISSING"


def count_frames(path: Path) -> int:
    frames = read(path, ":")
    return len(frames) if isinstance(frames, list) else 1


def tail(path: Path, n: int = 40) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(errors="replace").splitlines()[-n:]


def main() -> int:
    model_name = "li_mace_v1_3060ti"
    model_dir = ROOT / "models/local_finetuned_li_mace_v1"
    report = {
        "dataset_frames": {
            "train": count_frames(ROOT / "data/mace_datasets/li_mace_train.extxyz"),
            "valid": count_frames(ROOT / "data/mace_datasets/li_mace_valid.extxyz"),
            "test": count_frames(ROOT / "data/mace_datasets/li_mace_test.extxyz"),
        },
        "files": {
            "model": status(model_dir / f"{model_name}.model"),
            "lammps_model": status(model_dir / f"{model_name}.model-lammps.pt"),
            "stage_two_model": status(model_dir / f"{model_name}_stagetwo.model"),
        },
    }
    logs = sorted((ROOT / "logs").glob("local_finetune_*.log"))
    report["latest_combined_log"] = str(logs[-1].relative_to(ROOT)) if logs else None
    if logs:
        report["latest_combined_log_tail"] = tail(logs[-1])

    output = ROOT / "local_finetune_summary.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
