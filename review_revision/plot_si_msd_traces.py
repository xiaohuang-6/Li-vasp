#!/usr/bin/env python3
"""Plot print-readable MSD traces for the Supporting Information."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT
        / "results/review_revision/gpu_analysis_20260725_0116/review_md_msd_traces_sampled.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "manuscript/figures/review_md_extended_msd_xy_traces.png",
    )
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    colors = {
        "A_Perfect": "#0072B2",
        "B1_Monovacancy": "#E69F00",
        "B2_Divacancy": "#D55E00",
        "C_StoneWales": "#009E73",
        "D_SiGraphene": "#CC79A7",
    }
    labels = {
        "A_Perfect": "pristine",
        "B1_Monovacancy": "monovacancy",
        "B2_Divacancy": "divacancy",
        "C_StoneWales": "Stone-Wales",
        "D_SiGraphene": "Si4-graphene",
    }
    seed_styles = [
        ("-", "o"),
        ("--", "s"),
        (":", "^"),
    ]
    panels = (
        ("finetuned_reference", "(a) Reference fine-tuned model"),
        ("committee_model", "(b) Committee-model sensitivity"),
    )

    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                row["model_family"],
                row["structure"],
                row["model_seed"],
                row["seed"],
            )
        ].append(row)

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
    for ax, (model_family, title) in zip(axes, panels):
        panel_groups = [
            (key, values)
            for key, values in sorted(grouped.items())
            if key[0] == model_family
        ]
        max_time = 0.0
        style_index: dict[str, int] = defaultdict(int)
        for (_, structure, model_seed, velocity_seed), values in panel_groups:
            values.sort(key=lambda row: float(row["time_ps"]))
            max_time = max(max_time, float(values[-1]["time_ps"]))
            index = style_index[structure]
            style_index[structure] += 1
            linestyle, marker = seed_styles[index % len(seed_styles)]
            suffix = f"m{model_seed[-2:]}" if model_seed else f"v{velocity_seed[-2:]}"
            ax.plot(
                [float(row["time_ps"]) for row in values],
                [float(row["msd_xy_a2"]) for row in values],
                color=colors[structure],
                linestyle=linestyle,
                linewidth=1.45,
                marker=marker,
                markersize=2.6,
                markevery=max(1, len(values) // 14),
                markerfacecolor="white",
                markeredgewidth=0.7,
                label=f"{labels[structure]} {suffix}",
            )
        ax.set_title(title, fontsize=10, fontweight="bold", loc="left")
        ax.set_xlabel("Time (ps)")
        ax.set_xlim(0, max_time)
        ax.grid(color="#D0D0D0", linewidth=0.55, alpha=0.7)
        ax.legend(
            fontsize=6.1,
            ncol=1,
            frameon=True,
            facecolor="white",
            edgecolor="#BBBBBB",
            framealpha=0.92,
            loc="upper right",
            handlelength=2.8,
        )
    axes[0].set_ylabel(r"Li MSD$_{xy}$ ($\mathrm{\AA^2}$)")
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=300, facecolor="white")
    fig.savefig(args.output.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
