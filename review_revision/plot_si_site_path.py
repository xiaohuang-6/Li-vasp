#!/usr/bin/env python3
"""Regenerate the active Supporting Information site and path figures."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
FAMILIES = (
    ("A_Perfect", "pristine graphene"),
    ("B1_Monovacancy", "monovacancy graphene"),
    ("B2_Divacancy", "divacancy graphene"),
    ("C_StoneWales", "Stone-Wales graphene"),
    ("D_SiGraphene", "Si$_4$-graphene motif"),
)
SITE_LABELS = {
    "prior_li_xy": "initial Li site",
    "hollow_C3": "hollow C$_3$",
    "cell_center": "cell center",
    "top_central_C": "top C",
    "top_offset_C": "offset top C",
    "bridge_C_C": "C-C bridge",
    "si_cluster_centroid": "Si$_4$ centroid",
    "top_highest_Si": "top Si",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def site_label(value: str) -> str:
    return SITE_LABELS.get(value, value.replace("_", " "))


def plot_sites(rows: list[dict[str, str]], output: Path) -> None:
    figure, axes = plt.subplots(5, 1, figsize=(7.5, 8.5), sharex=True)
    for axis, (family, family_label) in zip(axes, FAMILIES, strict=True):
        selected = sorted(
            (row for row in rows if row["family"] == family and row["kind"] == "site"),
            key=lambda row: float(row["rel_to_site_min_ev"]),
        )
        colors = ["#0072B2" if index == 0 else "#D6DCE5" for index in range(len(selected))]
        axis.barh(
            [site_label(row["label"]) for row in selected],
            [float(row["rel_to_site_min_ev"]) for row in selected],
            color=colors,
            edgecolor="#333333",
            linewidth=0.4,
        )
        axis.invert_yaxis()
        axis.set_title(family_label, fontsize=9, loc="left")
        axis.set_xlim(0.0, 2.0)
        axis.grid(axis="x", color="#E8E8E8", linewidth=0.6)
        axis.tick_params(axis="both", labelsize=8)
    axes[-1].set_xlabel("Relative DFT single-point energy within each family (eV)")
    figure.suptitle("Fixed-geometry Li site-energy scan", fontsize=12)
    figure.tight_layout(rect=(0, 0, 1, 0.97))
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output.with_suffix(".png"), dpi=260)
    figure.savefig(output.with_suffix(".pdf"))
    plt.close(figure)


def plot_paths(rows: list[dict[str, str]], output: Path) -> None:
    figure, axes = plt.subplots(5, 2, figsize=(9.0, 9.2), sharex=True, sharey=False)
    panel_labels = "abcdefghij"
    for family_index, (family, family_label) in enumerate(FAMILIES):
        for path_index, path_id in enumerate(("path01", "path02")):
            axis = axes[family_index][path_index]
            selected = sorted(
                (
                    row
                    for row in rows
                    if row["family"] == family and row["path_id"] == path_id
                ),
                key=lambda row: float(row["reaction_index"]),
            )
            if not selected:
                raise ValueError(f"Missing path rows for {family}/{path_id}")
            axis.plot(
                [float(row["reaction_index"]) for row in selected],
                [float(row["rel_to_start_ev"]) for row in selected],
                marker="o",
                color="#0072B2",
                linewidth=1.5,
                markersize=3.5,
            )
            panel = panel_labels[family_index * 2 + path_index]
            start = site_label(selected[0]["path_start"])
            end = site_label(selected[0]["path_end"])
            axis.set_title(f"({panel}) {family_label}\n{start} to {end}", fontsize=8, loc="left")
            axis.axhline(0.0, color="#777777", linewidth=0.6)
            axis.grid(color="#ECECEC", linewidth=0.5)
            axis.tick_params(axis="both", labelsize=7)
            if path_index == 0:
                axis.set_ylabel("Relative to start (eV)", fontsize=8)
            if family_index == len(FAMILIES) - 1:
                axis.set_xlabel("Linear image index", fontsize=8)
    figure.suptitle("Fixed-geometry paths; energies are relative to each first image", fontsize=11)
    figure.tight_layout(rect=(0, 0, 1, 0.965))
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output.with_suffix(".png"), dpi=260)
    figure.savefig(output.with_suffix(".pdf"))
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-data",
        type=Path,
        default=ROOT / "submission_data/results/fixed_site_energies.csv",
    )
    parser.add_argument(
        "--path-data",
        type=Path,
        default=ROOT / "submission_data/results/fixed_path_profiles.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "manuscript/figures",
    )
    args = parser.parse_args()
    plot_sites(read_rows(args.site_data), args.output_dir / "site_energy_rankings_revised")
    plot_paths(read_rows(args.path_data), args.output_dir / "path_profiles_revised")
    print(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
