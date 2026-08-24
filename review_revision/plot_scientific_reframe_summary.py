#!/usr/bin/env python3
"""Plot the two evidence-backed findings for the resubmission narrative."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


DISPLAY_NAMES = {
    "A_Perfect": "Pristine",
    "B1_Monovacancy": "Monovacancy",
    "B2_Divacancy": "Divacancy",
    "C_StoneWales": "Stone-Wales",
    "D_SiGraphene": r"Si$_4$-graphene",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("submission_data/results"),
        help="Directory containing the curated submission CSV files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("manuscript/figures/scientific_summary_reframe"),
        help="Output path without extension.",
    )
    args = parser.parse_args()

    adsorption_rows = read_rows(args.results / "adsorption_energies.csv")
    foundation_rows = read_rows(
        args.results / "foundation_snapshot_force_summary.csv"
    )
    finetuned_rows = read_rows(
        args.results / "grouped_e0_snapshot_force_summary.csv"
    )

    families = list(DISPLAY_NAMES)
    adsorption = {
        row["family"]: float(row["adsorption_energy_ev_per_li"])
        for row in adsorption_rows
        if row["usable"].lower() == "true"
    }

    def snapshot_values(rows: list[dict[str, str]]) -> dict[str, float]:
        return {
            row["group"]: float(row["force_rmse_mev_a_frame_rms"])
            for row in rows
        }

    foundation = snapshot_values(foundation_rows)
    finetuned = snapshot_values(finetuned_rows)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 9,
            "legend.fontsize": 8.5,
            "axes.linewidth": 0.8,
        }
    )

    fig, (ax_ads, ax_force) = plt.subplots(
        1, 2, figsize=(9.0, 3.8), gridspec_kw={"width_ratios": (1.35, 1)}
    )

    colors = ["#4C78A8", "#2A9D8F", "#72B7B2", "#E9C46A", "#E76F51"]
    x_ads = np.arange(len(families))
    y_ads = [adsorption[family] for family in families]
    bars = ax_ads.bar(x_ads, y_ads, color=colors, edgecolor="#222222", linewidth=0.6)
    ax_ads.axhline(0.0, color="#222222", linewidth=0.8)
    ax_ads.set_xticks(x_ads, [DISPLAY_NAMES[family] for family in families])
    ax_ads.tick_params(axis="x", rotation=25)
    ax_ads.set_ylabel(r"$E_{\mathrm{ads}}$ (eV per Li)")
    ax_ads.set_title("a  Local-environment-dependent Li adsorption", loc="left", weight="bold")
    ax_ads.set_ylim(-3.75, 0.65)
    ax_ads.grid(axis="y", color="#D9D9D9", linewidth=0.6, alpha=0.8)
    ax_ads.set_axisbelow(True)
    for bar, value in zip(bars, y_ads):
        y_text = value - 0.13 if value < -0.15 else value + 0.09
        va = "top" if value < -0.15 else "bottom"
        ax_ads.text(
            bar.get_x() + bar.get_width() / 2,
            y_text,
            f"{value:.2f}",
            ha="center",
            va=va,
            fontsize=8,
        )

    groups = ["B1_Monovacancy", "D_SiGraphene"]
    labels = [DISPLAY_NAMES[group] for group in groups]
    x_force = np.arange(len(groups))
    width = 0.34
    base_values = [foundation[group] for group in groups]
    tuned_values = [finetuned[group] for group in groups]
    base_bars = ax_force.bar(
        x_force - width / 2,
        base_values,
        width,
        label="MACE-MPA-0",
        color="#A0A0A0",
        edgecolor="#222222",
        linewidth=0.6,
    )
    tuned_bars = ax_force.bar(
        x_force + width / 2,
        tuned_values,
        width,
        label="Fine-tuned grouped-E0",
        color="#2A9D8F",
        edgecolor="#222222",
        linewidth=0.6,
    )
    ax_force.set_xticks(x_force, labels)
    ax_force.set_ylabel(r"DFT snapshot force RMSE (meV $\mathrm{\AA}^{-1}$)")
    ax_force.set_title("b  Environment-resolved extrapolation", loc="left", weight="bold")
    ax_force.set_ylim(0, 1300)
    ax_force.grid(axis="y", color="#D9D9D9", linewidth=0.6, alpha=0.8)
    ax_force.set_axisbelow(True)
    ax_force.legend(frameon=False, loc="upper right")

    for bar_group in (base_bars, tuned_bars):
        for bar in bar_group:
            value = bar.get_height()
            ax_force.text(
                bar.get_x() + bar.get_width() / 2,
                value + 24,
                f"{value:.0f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    reductions = [
        100.0 * (foundation[group] - finetuned[group]) / foundation[group]
        for group in groups
    ]
    ax_force.text(
        x_force[0],
        620,
        f"{reductions[0]:.0f}% reduction",
        ha="center",
        va="center",
        fontsize=8,
        color="#444444",
    )
    ax_force.text(
        x_force[1],
        205,
        f"{reductions[1]:.0f}% reduction",
        ha="center",
        va="center",
        fontsize=8,
        color="#1D6F63",
        weight="bold",
    )

    for ax in (ax_ads, ax_force):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.tight_layout(w_pad=2.2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix(".png"), dpi=350, bbox_inches="tight")
    fig.savefig(args.output.with_suffix(".pdf"), bbox_inches="tight")


if __name__ == "__main__":
    main()
