#!/usr/bin/env python3
"""Build a science-centered graphical abstract from curated strict evidence."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np


FAMILIES = (
    ("A_Perfect", "Pristine", "#4C78A8"),
    ("B1_Monovacancy", "Mono-\nvacancy", "#2A9D8F"),
    ("B2_Divacancy", "Di-\nvacancy", "#72B7B2"),
    ("C_StoneWales", "Stone-\nWales", "#E9C46A"),
    ("D_SiGraphene", "Si$_4$-\ngraphene", "#E76F51"),
)
MODELS = (
    ("foundation_mpa0", "MACE-MPA-0", "#6B7280"),
    ("grouped_e0", "Fine-tuned grouped-$E_0$", "#0072B2"),
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def one(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(row.get(key) == value for key, value in criteria.items())
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one row for {criteria}; found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--structures",
        type=Path,
        default=Path("manuscript/figures/structure_models.png"),
    )
    parser.add_argument(
        "--site-data",
        type=Path,
        default=Path("submission_data/results/d3_site_adsorption_energies.csv"),
    )
    parser.add_argument(
        "--balanced-summary",
        type=Path,
        default=Path("submission_data/results/balanced_perturbation_force_summary.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("manuscript/graphical_abstract.png"),
    )
    args = parser.parse_args()

    site_rows = [
        row for row in read_rows(args.site_data) if row["usable"].lower() == "true"
    ]
    balanced_rows = read_rows(args.balanced_summary)
    for family, _, _ in FAMILIES:
        family_sites = [row for row in site_rows if row["family"] == family]
        if len(family_sites) != 3:
            raise ValueError(
                f"Expected three strictly usable D3 sites for {family}; "
                f"found {len(family_sites)}"
            )
        if any(
            not math.isfinite(float(row["adsorption_energy_ev_per_li"]))
            for row in family_sites
        ):
            raise ValueError(f"Non-finite adsorption energy for {family}")
    pristine_energies = [
        float(row["adsorption_energy_ev_per_li"])
        for row in site_rows
        if row["family"] == "A_Perfect"
    ]
    non_pristine_energies = [
        float(row["adsorption_energy_ev_per_li"])
        for row in site_rows
        if row["family"] != "A_Perfect"
    ]
    non_pristine_gap = min(pristine_energies) - max(non_pristine_energies)
    if non_pristine_gap <= 0:
        raise ValueError("Non-pristine and pristine adsorption ranges overlap")

    all_force_rmse = {
        model: float(
            one(balanced_rows, model=model, family="ALL")[
                "force_rmse_mev_a_pooled"
            ]
        )
        for model, _, _ in MODELS
    }
    reduction = 100.0 * (
        all_force_rmse["foundation_mpa0"] - all_force_rmse["grouped_e0"]
    ) / all_force_rmse["foundation_mpa0"]

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 9,
            "axes.linewidth": 0.8,
        }
    )
    fig = plt.figure(figsize=(12, 4.8), dpi=300, facecolor="white")
    grid = fig.add_gridspec(
        3,
        2,
        height_ratios=(0.18, 0.70, 1.15),
        width_ratios=(1.0, 1.1),
        hspace=0.12,
        wspace=0.22,
        left=0.055,
        right=0.985,
        top=0.96,
        bottom=0.10,
    )

    title_axis = fig.add_subplot(grid[0, :])
    title_axis.axis("off")
    title_axis.text(
        0.5,
        0.62,
        "Local chemistry shapes Li adsorption and MLIP transferability",
        ha="center",
        va="center",
        fontsize=21,
        weight="bold",
        color="#202936",
    )

    structure_axis = fig.add_subplot(grid[1, :])
    structure_axis.imshow(mpimg.imread(args.structures))
    structure_axis.set_axis_off()

    x = np.arange(len(FAMILIES), dtype=float)
    adsorption_axis = fig.add_subplot(grid[2, 0])
    rank_markers = ((1, "o"), (2, "s"), (3, "^"))
    jitter = (-0.13, 0.0, 0.13)
    for family_index, (family, _, color) in enumerate(FAMILIES):
        rows = sorted(
            (row for row in site_rows if row["family"] == family),
            key=lambda row: int(row["pbe_fixed_site_rank"]),
        )
        values = [float(row["adsorption_energy_ev_per_li"]) for row in rows]
        adsorption_axis.plot(
            [x[family_index], x[family_index]],
            [min(values), max(values)],
            color="#737982",
            linewidth=1.2,
            zorder=1,
        )
        for offset, row, (_, marker) in zip(jitter, rows, rank_markers, strict=True):
            adsorption_axis.scatter(
                x[family_index] + offset,
                float(row["adsorption_energy_ev_per_li"]),
                s=42,
                marker=marker,
                color=color,
                edgecolor="#222222",
                linewidth=0.55,
                zorder=3,
            )
    adsorption_axis.axhline(0, color="#222222", linewidth=0.8)
    adsorption_axis.set_xticks(x, [label for _, label, _ in FAMILIES])
    adsorption_axis.set_ylabel(r"$E_{\mathrm{ads}}$ (eV per Li)")
    adsorption_axis.set_title(
        "Three fixed-geometry sites per family", loc="left", weight="bold"
    )
    for rank, marker in rank_markers:
        adsorption_axis.scatter(
            [],
            [],
            s=35,
            marker=marker,
            color="#8A8F98",
            edgecolor="#222222",
            linewidth=0.5,
            label=f"PBE rank {rank}",
        )
    adsorption_axis.legend(frameon=False, ncol=3, fontsize=7.2, loc="lower left")
    adsorption_axis.text(
        0.02,
        0.90,
        "All non-pristine sites are\n"
        f"at least {non_pristine_gap:.3f} eV more favorable",
        transform=adsorption_axis.transAxes,
        ha="left",
        va="top",
        fontsize=8.3,
        weight="bold",
        color="#202936",
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5},
    )
    adsorption_axis.grid(axis="y", color="#D9DDE2", linewidth=0.6)
    adsorption_axis.spines[["top", "right"]].set_visible(False)
    adsorption_axis.set_axisbelow(True)

    force_axis = fig.add_subplot(grid[2, 1])
    width = 0.34
    maximum = 0.0
    for model_index, (model, label, color) in enumerate(MODELS):
        values = [
            float(
                one(balanced_rows, model=model, family=family)[
                    "force_rmse_mev_a_pooled"
                ]
            )
            for family, _, _ in FAMILIES
        ]
        maximum = max(maximum, max(values))
        bars = force_axis.bar(
            x + (model_index - 0.5) * width,
            values,
            width=width,
            color=color,
            edgecolor="#222222",
            linewidth=0.5,
            label=label,
        )
        force_axis.bar_label(
            bars,
            labels=[f"{value:.0f}" for value in values],
            padding=2,
            fontsize=7.5,
        )
    force_axis.set_ylim(0, maximum * 1.26)
    force_axis.set_xticks(x, [label for _, label, _ in FAMILIES])
    force_axis.set_ylabel(r"Pooled force RMSE (meV $\mathrm{\AA}^{-1}$)")
    force_axis.set_title(
        "Predefined local perturbation benchmark", loc="left", weight="bold"
    )
    force_axis.text(
        0.98,
        0.92,
        f"Overall: {all_force_rmse['foundation_mpa0']:.1f} to "
        f"{all_force_rmse['grouped_e0']:.1f} meV $\mathrm{{\AA}}^{{-1}}$ "
        f"({reduction:.1f}% lower)",
        transform=force_axis.transAxes,
        ha="right",
        va="top",
        fontsize=8.5,
        weight="bold",
        color="#202936",
    )
    force_axis.legend(frameon=False, fontsize=8, loc="upper left")
    force_axis.grid(axis="y", color="#D9DDE2", linewidth=0.6)
    force_axis.spines[["top", "right"]].set_visible(False)
    force_axis.set_axisbelow(True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=300, facecolor="white")
    plt.close(fig)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
