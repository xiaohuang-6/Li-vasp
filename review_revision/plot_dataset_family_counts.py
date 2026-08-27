#!/usr/bin/env python3
"""Regenerate the Supporting Information dataset-family count figure."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
FAMILIES = (
    ("A_Perfect", "Pristine"),
    ("B1_Monovacancy", "Mono-\nvacancy"),
    ("B2_Divacancy", "Di-\nvacancy"),
    ("C_StoneWales", "Stone-\nWales"),
    ("D_SiGraphene", "Si$_4$-\ngraphene"),
)
FAMILY_RE = re.compile(r"\bfamily=(?:\"([^\"]+)\"|(\S+))")


def count_families(paths: list[Path]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            match = FAMILY_RE.search(line)
            if match:
                counts[match.group(1) or match.group(2)] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split-dir",
        type=Path,
        default=ROOT / "submission_data/datasets/grouped_split",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "manuscript/figures/dataset_family_counts.png",
    )
    args = parser.parse_args()

    split_paths = [args.split_dir / f"{name}.extxyz" for name in ("train", "valid", "test")]
    missing = [path for path in split_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing grouped split files: {missing}")
    counts = count_families(split_paths)
    if sum(counts.values()) != 273 or set(counts) != {family for family, _ in FAMILIES}:
        raise ValueError(f"Unexpected family counts: {dict(counts)}")

    labels = [label for _, label in FAMILIES]
    values = [counts[family] for family, _ in FAMILIES]
    colors = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00")
    fig, axis = plt.subplots(figsize=(8.0, 4.0), constrained_layout=True)
    bars = axis.bar(labels, values, color=colors, edgecolor="#222222", linewidth=0.6)
    axis.bar_label(bars, padding=3, fontsize=9)
    axis.set_ylabel("DFT-labeled configurations")
    axis.set_title("Dataset composition by local structural family", loc="left", weight="bold")
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#D6D9DE", linewidth=0.6)
    axis.set_axisbelow(True)
    axis.set_ylim(0, max(values) * 1.18)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=200, facecolor="white")
    plt.close(fig)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
