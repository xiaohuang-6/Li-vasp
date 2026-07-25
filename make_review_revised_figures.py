#!/usr/bin/env python3
"""Build conservative figures for the review-revised manuscript.

The first draft used path-scan quantities and wrapped Li displacements too
aggressively. These plots keep the same evidence but label it as what it is:
DFT endpoint/path-scan energetics, MACE split errors, and MD stability
diagnostics.
"""

from __future__ import annotations

from pathlib import Path
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "two_day_rush"
REVIEW_GPU = ROOT / "results" / "review_revision" / "gpu_analysis"
FIGS = ROOT / "manuscript" / "figures"

FAMILY_LABELS = {
    "A_Perfect": "pristine graphene",
    "B1_Monovacancy": "monovacancy graphene",
    "B2_Divacancy": "divacancy graphene",
    "C_StoneWales": "Stone-Wales graphene",
    "D_SiGraphene": "Si4-graphene motif",
}

SITE_LABELS = {
    "prior_li_xy": "initial Li site",
    "hollow_C3": "hollow C3",
    "cell_center": "cell center",
    "top_central_C": "top C",
    "top_offset_C": "offset top C",
    "bridge_C_C": "C-C bridge",
    "si_cluster_centroid": "Si4 centroid",
    "top_highest_Si": "top Si",
}


def label_site(value: str) -> str:
    return SITE_LABELS.get(value, value.replace("_", " "))


def make_site_energetics() -> None:
    df = pd.read_csv(RESULTS / "site_energy_rankings.csv")
    df = df[df["kind"].eq("site")].copy()
    df["family_label"] = df["family"].map(FAMILY_LABELS)
    df["site_label"] = df["label"].map(label_site)

    families = list(FAMILY_LABELS)
    fig, axes = plt.subplots(len(families), 1, figsize=(7.5, 8.5), sharex=True)
    for ax, family in zip(axes, families, strict=True):
        sub = df[df["family"].eq(family)].sort_values("rel_to_site_min_ev")
        colors = ["#4C78A8" if i == 0 else "#D6DCE5" for i in range(len(sub))]
        ax.barh(sub["site_label"], sub["rel_to_site_min_ev"], color=colors, edgecolor="#333333", linewidth=0.4)
        ax.invert_yaxis()
        ax.set_title(FAMILY_LABELS[family], fontsize=9, loc="left")
        ax.set_xlim(0.0, 2.0)
        ax.grid(axis="x", color="#e8e8e8", linewidth=0.6)
        ax.tick_params(axis="both", labelsize=8)
    axes[-1].set_xlabel("Relative DFT single-point energy within each family (eV)")
    fig.suptitle("Fixed-geometry Li site energy scan", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(FIGS / "site_energy_rankings_revised.png", dpi=260)
    fig.savefig(FIGS / "site_energy_rankings_revised.pdf")
    plt.close(fig)


def make_path_profiles() -> None:
    df = pd.read_csv(RESULTS / "path_profiles.csv")
    families = list(FAMILY_LABELS)
    path_ids = ["path01", "path02"]
    fig, axes = plt.subplots(len(families), len(path_ids), figsize=(9.0, 9.2), sharex=True, sharey=False)
    for row, family in enumerate(families):
        for col, path_id in enumerate(path_ids):
            ax = axes[row][col]
            sub = df[df["family"].eq(family) & df["path_id"].eq(path_id)].sort_values("reaction_index")
            if sub.empty:
                ax.axis("off")
                continue
            ax.plot(sub["reaction_index"], sub["rel_to_start_ev"], marker="o", color="#2F6F8F", linewidth=1.5, markersize=3.5)
            start = label_site(str(sub["path_start"].iloc[0]))
            end = label_site(str(sub["path_end"].iloc[0]))
            ax.set_title(f"{FAMILY_LABELS[family]}\n{start} -> {end}", fontsize=8)
            ax.axhline(0.0, color="#777777", linewidth=0.6)
            ax.grid(color="#ececec", linewidth=0.5)
            ax.tick_params(axis="both", labelsize=7)
            if col == 0:
                ax.set_ylabel("Relative to start (eV)", fontsize=8)
            if row == len(families) - 1:
                ax.set_xlabel("Linear image index", fontsize=8)
    fig.suptitle("Fixed-geometry path scans; monotonic paths report endpoint energy differences, not activation barriers", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(FIGS / "path_profiles_revised.png", dpi=260)
    fig.savefig(FIGS / "path_profiles_revised.pdf")
    plt.close(fig)


def make_mace_error_plot() -> None:
    df = pd.read_csv(RESULTS / "mace_error_table_final.csv")
    tv = df[df["section"].eq("train_valid")].copy()
    test = df[df["section"].eq("test") & df["config_type"].str.endswith("_Default") & ~df["config_type"].str.startswith("SP_")].copy()
    test["family"] = test["config_type"].str.replace("_Default", "", regex=False)
    test["family_label"] = test["family"].map(FAMILY_LABELS)

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6))
    axes[0].bar(tv["config_type"].str.replace("_Default", "", regex=False), tv["rmse_f_mev_a"], color=["#7AA6C2", "#D28A5E"])
    axes[0].set_ylabel("Force RMSE (meV/A)")
    axes[0].set_title("Train/validation force error")
    axes[0].grid(axis="y", color="#ececec", linewidth=0.6)

    axes[1].barh(test["family_label"], test["rmse_f_mev_a"], color="#8FAF80", edgecolor="#333333", linewidth=0.4)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Force RMSE (meV/A)")
    axes[1].set_title("Held-out test split by family")
    axes[1].grid(axis="x", color="#ececec", linewidth=0.6)
    for ax in axes:
        ax.tick_params(axis="both", labelsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "mace_error_diagnostics_revised.png", dpi=260)
    fig.savefig(FIGS / "mace_error_diagnostics_revised.pdf")
    plt.close(fig)


def make_md_stability_plot() -> None:
    df = pd.read_csv(RESULTS / "md" / "md_summary.csv")
    df400 = df[df["target_temperature_k"].eq(400.0)].copy()
    df400["family_label"] = df400["case"].map(FAMILY_LABELS)
    df400["drift_abs"] = df400["total_energy_drift_ev_atom_assuming_last_natoms"].abs()

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.8))
    colors = ["#B04A4A" if case in {"B1_Monovacancy", "B2_Divacancy"} else "#6A8CAF" for case in df400["case"]]
    axes[0].barh(df400["family_label"], df400["total_energy_drift_ev_atom_assuming_last_natoms"], color=colors)
    axes[0].axvline(0.0, color="#333333", linewidth=0.8)
    axes[0].set_xlabel("Total-energy drift per atom (eV/atom)")
    axes[0].set_title("400 K NVT energy-drift diagnostic")
    axes[0].invert_yaxis()
    axes[0].grid(axis="x", color="#ececec", linewidth=0.6)

    axes[1].barh(df400["family_label"], df400["mean_temperature_k"], xerr=df400["std_temperature_k"], color=colors, alpha=0.85)
    axes[1].axvline(400.0, color="#333333", linestyle="--", linewidth=0.8)
    axes[1].set_xlabel("Temperature (K)")
    axes[1].set_title("400 K NVT temperature diagnostic")
    axes[1].invert_yaxis()
    axes[1].grid(axis="x", color="#ececec", linewidth=0.6)
    for ax in axes:
        ax.tick_params(axis="both", labelsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "md_stability_diagnostics_revised.png", dpi=260)
    fig.savefig(FIGS / "md_stability_diagnostics_revised.pdf")
    plt.close(fig)


def copy_review_gpu_figures() -> None:
    """Stage reviewer GPU diagnostics for the manuscript figure folder."""
    figure_map = {
        "mace_test_force_rmse_comparison.png": "review_mace_foundation_comparison.png",
        "review_md_msd_xy_traces.png": "review_md_unwrapped_msd_xy_traces.png",
        "review_md_short_diffusion_xy.png": "review_md_short_dxy_diagnostics.png",
    }
    for source_name, target_name in figure_map.items():
        source = REVIEW_GPU / source_name
        if not source.exists():
            print(f"Skipping missing reviewer GPU figure: {source}")
            continue
        shutil.copy2(source, FIGS / target_name)


def main() -> int:
    FIGS.mkdir(parents=True, exist_ok=True)
    make_site_energetics()
    make_path_profiles()
    make_mace_error_plot()
    make_md_stability_plot()
    copy_review_gpu_figures()
    print(f"Wrote revised figures to {FIGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
