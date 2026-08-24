#!/usr/bin/env python3
"""Build a science-centered graphical abstract from curated local evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--structures",
        type=Path,
        default=Path("manuscript/figures/structure_models.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("manuscript/graphical_abstract.png"),
    )
    args = parser.parse_args()

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.titlesize": 16,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )

    fig = plt.figure(figsize=(12, 4.8), facecolor="white")
    grid = fig.add_gridspec(
        3,
        2,
        height_ratios=(0.23, 0.92, 1.05),
        width_ratios=(1.3, 1),
        hspace=0.12,
        wspace=0.18,
    )

    title_ax = fig.add_subplot(grid[0, :])
    title_ax.axis("off")
    title_ax.text(
        0.5,
        0.65,
        "Defect chemistry links Li adsorption and MLIP transferability",
        ha="center",
        va="center",
        fontsize=23,
        weight="bold",
        color="#202936",
    )

    structure_ax = fig.add_subplot(grid[1, :])
    structure_ax.imshow(mpimg.imread(args.structures))
    structure_ax.set_axis_off()

    adsorption_ax = fig.add_subplot(grid[2, 0])
    names = ["Pristine", "Mono-\nvacancy", "Di-\nvacancy", "Stone-\nWales", "Si$_4$-\ngraphene"]
    values = [-0.634, -3.115, -1.328, 0.009, -3.349]
    colors = ["#4C78A8", "#2A9D8F", "#72B7B2", "#E9C46A", "#E76F51"]
    x = np.arange(len(names))
    bars = adsorption_ax.bar(
        x, values, color=colors, edgecolor="#222222", linewidth=0.7
    )
    adsorption_ax.axhline(0, color="#222222", linewidth=0.9)
    adsorption_ax.set_xticks(x, names)
    adsorption_ax.set_ylabel(r"$E_{\mathrm{ads}}$ (eV per Li)")
    adsorption_ax.set_title("Defects reshape dilute Li adsorption", loc="left", weight="bold")
    adsorption_ax.set_ylim(-3.75, 0.55)
    adsorption_ax.grid(axis="y", color="#D9D9D9", linewidth=0.6)
    adsorption_ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        y_text = value - 0.13 if value < -0.15 else value + 0.08
        adsorption_ax.text(
            bar.get_x() + bar.get_width() / 2,
            y_text,
            f"{value:.2f}",
            ha="center",
            va="top" if value < -0.15 else "bottom",
            fontsize=10,
        )
    adsorption_ax.spines["top"].set_visible(False)
    adsorption_ax.spines["right"].set_visible(False)

    transfer_ax = fig.add_subplot(grid[2, 1])
    transfer_ax.set_xlim(0, 1)
    transfer_ax.set_ylim(0, 1)
    transfer_ax.axis("off")
    transfer_ax.text(
        0.0,
        0.98,
        "Fine-tuning response depends on local environment",
        ha="left",
        va="top",
        fontsize=16,
        weight="bold",
    )

    rows = [
        (0.67, "Si$_4$-graphene", 310, 114, "63% lower", "#2A9D8F"),
        (0.32, "Monovacancy", 1149, 1107, "4% lower", "#C84B31"),
    ]
    for y, label, before, after, change, color in rows:
        transfer_ax.text(0.02, y + 0.13, label, fontsize=14, weight="bold", va="center")
        transfer_ax.text(
            0.08,
            y,
            f"{before}",
            fontsize=18,
            weight="bold",
            ha="center",
            va="center",
            color="#666666",
        )
        arrow = FancyArrowPatch(
            (0.18, y),
            (0.55, y),
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=2.4,
            color=color,
        )
        transfer_ax.add_patch(arrow)
        transfer_ax.text(
            0.64,
            y,
            f"{after}",
            fontsize=18,
            weight="bold",
            ha="center",
            va="center",
            color=color,
        )
        transfer_ax.text(
            0.86,
            y,
            change,
            fontsize=12,
            weight="bold",
            ha="center",
            va="center",
            color=color,
        )

    transfer_ax.text(
        0.5,
        0.05,
        r"DFT snapshot force RMSE (meV $\mathrm{\AA}^{-1}$)",
        ha="center",
        va="center",
        fontsize=11,
        color="#333333",
    )

    fig.savefig(args.output, dpi=300, facecolor="white")


if __name__ == "__main__":
    main()
