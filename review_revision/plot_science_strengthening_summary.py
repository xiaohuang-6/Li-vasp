#!/usr/bin/env python3
"""Plot multi-site adsorption and two complementary MACE force benchmarks."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


FAMILIES = (
    ("A_Perfect", "Pristine"),
    ("B1_Monovacancy", "Mono-\nvacancy"),
    ("B2_Divacancy", "Di-\nvacancy"),
    ("C_StoneWales", "Stone-\nWales"),
    ("D_SiGraphene", "Si$_4$-\ngraphene"),
)
MODEL_STYLES = (
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


def style_axis(axis: plt.Axes) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#D6D9DE", linewidth=0.6)
    axis.set_axisbelow(True)
    axis.tick_params(length=3, width=0.7)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("submission_data/results"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("manuscript/figures/scientific_summary_strengthened"),
    )
    args = parser.parse_args()

    site_rows = [
        row
        for row in read_rows(args.results / "d3_site_adsorption_energies.csv")
        if row["usable"].lower() == "true"
    ]
    balanced_frames = read_rows(args.results / "balanced_perturbation_force_errors.csv")
    balanced_summary = read_rows(args.results / "balanced_perturbation_force_summary.csv")
    foundation_challenge = read_rows(
        args.results / "foundation_snapshot_force_summary.csv"
    )
    tuned_challenge = read_rows(
        args.results / "grouped_e0_snapshot_force_summary.csv"
    )
    foundation_challenge_frames = read_rows(
        args.results / "foundation_snapshot_force_errors.csv"
    )
    tuned_challenge_frames = read_rows(
        args.results / "grouped_e0_snapshot_force_errors.csv"
    )

    for family, _ in FAMILIES:
        count = sum(row["family"] == family for row in site_rows)
        if count != 3:
            raise ValueError(f"Expected three usable D3 sites for {family}; found {count}")

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.4,
            "axes.linewidth": 0.8,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.2))
    axis_ads, axis_balanced = axes[0]
    axis_amplitude, axis_challenge = axes[1]

    x = np.arange(len(FAMILIES), dtype=float)
    jitter = (-0.13, 0.0, 0.13)
    site_color = "#009E73"
    rank_markers = ((1, "o"), (2, "s"), (3, "^"))
    for family_index, (family, _) in enumerate(FAMILIES):
        family_sites = sorted(
            (row for row in site_rows if row["family"] == family),
            key=lambda row: int(row["pbe_fixed_site_rank"]),
        )
        site_values = [float(row["adsorption_energy_ev_per_li"]) for row in family_sites]
        axis_ads.plot(
            [x[family_index], x[family_index]],
            [min(site_values), max(site_values)],
            color="#8A8F98",
            linewidth=1.0,
            zorder=1,
        )
        for offset, row, (_, marker) in zip(
            jitter, family_sites, rank_markers, strict=True
        ):
            axis_ads.scatter(
                x[family_index] + offset,
                float(row["adsorption_energy_ev_per_li"]),
                s=30,
                marker=marker,
                color=site_color,
                edgecolor="#222222",
                linewidth=0.5,
                zorder=3,
            )
    axis_ads.axhline(0.0, color="#222222", linewidth=0.7)
    axis_ads.set_xticks(x, [label for _, label in FAMILIES])
    axis_ads.set_ylabel(r"$E_{\mathrm{ads}}$ (eV per Li)")
    axis_ads.set_title("(a) Li adsorption across sites", loc="left", weight="bold")
    for rank, marker in rank_markers:
        axis_ads.scatter(
            [], [], s=30, marker=marker, color=site_color, edgecolor="#222222",
            linewidth=0.5, label=f"PBE site rank {rank}"
        )
    axis_ads.legend(frameon=False, loc="best")
    style_axis(axis_ads)

    width = 0.34
    family_labels = [label for _, label in FAMILIES]
    for model_index, (model, label, color) in enumerate(MODEL_STYLES):
        offsets = x + (model_index - 0.5) * width
        values = [
            float(
                one(
                    balanced_summary,
                    model=model,
                    family=family,
                )["force_rmse_mev_a_pooled"]
            )
            for family, _ in FAMILIES
        ]
        bars = axis_balanced.bar(
            offsets,
            values,
            width=width,
            color=color,
            edgecolor="#222222",
            linewidth=0.45,
            label=label,
            zorder=2,
        )
        for family_index, (family, _) in enumerate(FAMILIES):
            points = [
                float(row["force_rmse_mev_a"])
                for row in balanced_frames
                if row["model"] == model and row["family"] == family
            ]
            if len(points) != 5:
                raise ValueError(
                    f"Expected five balanced frames for {model}/{family}; found {len(points)}"
                )
            point_x = np.linspace(-0.10, 0.10, len(points)) * width + offsets[family_index]
            axis_balanced.scatter(
                point_x,
                points,
                s=8,
                facecolor="white",
                edgecolor="#222222",
                linewidth=0.45,
                zorder=3,
            )
        axis_balanced.bar_label(
            bars,
            labels=[f"{value:.0f}" for value in values],
            padding=-13,
            fontsize=6.8,
            color="white",
            weight="bold",
        )
    axis_balanced.set_xticks(x, family_labels)
    axis_balanced.set_ylabel(r"Force RMSE (meV $\mathrm{\AA}^{-1}$)")
    axis_balanced.set_title(
        "(b) Family-balanced perturbations", loc="left", weight="bold"
    )
    axis_balanced.set_ylim(0, 650)
    axis_balanced.legend(
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=2,
        columnspacing=0.8,
        handletextpad=0.5,
    )
    style_axis(axis_balanced)

    sigmas = np.asarray((0.03, 0.06, 0.10), dtype=float)
    for model, label, color in MODEL_STYLES:
        values = []
        for sigma in sigmas:
            rows = [
                row
                for row in balanced_frames
                if row["model"] == model
                and np.isclose(float(row["sigma_a"]), sigma)
            ]
            expected = 5 if np.isclose(sigma, 0.03) else 10
            if len(rows) != expected:
                raise ValueError(
                    f"Expected {expected} balanced frames for {model}/sigma={sigma}; "
                    f"found {len(rows)}"
                )
            squared_error_sum = sum(
                float(row["force_rmse_mev_a"]) ** 2 * 3 * int(row["natoms"])
                for row in rows
            )
            component_count = sum(3 * int(row["natoms"]) for row in rows)
            values.append(np.sqrt(squared_error_sum / component_count))
        axis_amplitude.plot(
            sigmas,
            values,
            color=color,
            linewidth=1.6,
            marker="o",
            markersize=4.5,
            label=label,
        )
        for sigma, value in zip(sigmas, values, strict=True):
            axis_amplitude.annotate(
                f"{value:.0f}",
                (sigma, value),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                fontsize=6.8,
            )
    axis_amplitude.set_xticks(sigmas, ("0.03", "0.06", "0.10"))
    axis_amplitude.set_xlabel(r"Perturbation standard deviation ($\mathrm{\AA}$)")
    axis_amplitude.set_ylabel(r"Pooled force RMSE (meV $\mathrm{\AA}^{-1}$)")
    axis_amplitude.set_title(
        "(c) Displacement-amplitude dependence", loc="left", weight="bold"
    )
    axis_amplitude.legend(frameon=False, loc="best")
    style_axis(axis_amplitude)

    challenge_groups = ("B1_Monovacancy", "D_SiGraphene")
    challenge_x = np.arange(2, dtype=float)
    challenge_sources = {
        "foundation_mpa0": foundation_challenge,
        "grouped_e0": tuned_challenge,
    }
    challenge_frame_sources = {
        "foundation_mpa0": foundation_challenge_frames,
        "grouped_e0": tuned_challenge_frames,
    }
    for model_index, (model, label, color) in enumerate(MODEL_STYLES):
        offsets = challenge_x + (model_index - 0.5) * width
        values = [
            float(one(challenge_sources[model], group=group)["force_rmse_mev_a_frame_rms"])
            for group in challenge_groups
        ]
        bars = axis_challenge.bar(
            offsets,
            values,
            width=width,
            color=color,
            edgecolor="#222222",
            linewidth=0.45,
        )
        for group_index, group in enumerate(challenge_groups):
            points = [
                float(row["force_rmse_mev_a"])
                for row in challenge_frame_sources[model]
                if row["case"] == group
            ]
            expected = 3 if group == "B1_Monovacancy" else 6
            if len(points) != expected:
                raise ValueError(
                    f"Expected {expected} challenge frames for {model}/{group}; "
                    f"found {len(points)}"
                )
            point_x = (
                np.linspace(-0.10, 0.10, len(points)) * width + offsets[group_index]
            )
            axis_challenge.scatter(
                point_x,
                points,
                s=9,
                facecolor="white",
                edgecolor="#222222",
                linewidth=0.45,
                zorder=3,
            )
        axis_challenge.bar_label(
            bars,
            labels=[f"{value:.0f}" for value in values],
            padding=-14,
            fontsize=7,
            color="white",
            weight="bold",
        )
    axis_challenge.set_xticks(challenge_x, ("Mono-\nvacancy", "Si$_4$-\ngraphene"))
    axis_challenge.set_ylabel(r"Force RMSE (meV $\mathrm{\AA}^{-1}$)")
    axis_challenge.set_title(
        "(d) High-displacement force comparison", loc="left", weight="bold"
    )
    style_axis(axis_challenge)

    fig.tight_layout(pad=0.8, w_pad=1.2, h_pad=1.5)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(args.output.with_suffix(".png"), dpi=400, bbox_inches="tight")
    print(args.output.with_suffix(".pdf"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
