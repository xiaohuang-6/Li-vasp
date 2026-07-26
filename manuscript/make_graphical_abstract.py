#!/usr/bin/env python3
"""Build the data-derived graphical abstract for the submission package."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
MACE_CSV = (
    ROOT
    / "results"
    / "review_revision"
    / "gpu_analysis_20260725_0116"
    / "mace_eval_summary.csv"
)
ADSORPTION_CSV = (
    ROOT
    / "results"
    / "review_revision"
    / "adsorption_energy_analysis"
    / "adsorption_energies.csv"
)
STRUCTURE_FIGURE = MANUSCRIPT / "figures" / "structure_models.png"

INK = "#202A35"
BLUE = "#2673A8"
ORANGE = "#E07831"
GREEN = "#2A7F62"
RED = "#B04A4A"
PANEL = "#F4F7F9"
LINE = "#B8C4CC"
OUTPUT_DPI = 300


def rounded_panel(ax: plt.Axes, edge: str = LINE) -> None:
    ax.set_axis_off()
    ax.add_patch(
        FancyBboxPatch(
            (0.01, 0.02),
            0.98,
            0.96,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            transform=ax.transAxes,
            facecolor=PANEL,
            edgecolor=edge,
            linewidth=1.4,
            zorder=-10,
        )
    )


def add_step_title(ax: plt.Axes, number: str, title: str) -> None:
    ax.text(
        0.05,
        0.91,
        number,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=15,
        fontweight="bold",
        color="white",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": BLUE, "edgecolor": BLUE},
    )
    ax.text(
        0.16,
        0.91,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=15,
        fontweight="bold",
        color=INK,
    )


def main() -> int:
    mace = pd.read_csv(MACE_CSV)
    adsorption = pd.read_csv(ADSORPTION_CSV)

    def force_rmse(model: str) -> float:
        row = mace[
            mace["model_label"].eq(model)
            & mace["split"].eq("test")
            & mace["family"].eq("ALL")
        ]
        if len(row) != 1:
            raise ValueError(f"Expected one all-family test row for {model}")
        return float(row.iloc[0]["force_rmse_mev_a_frame_rms"])

    foundation_rmse = force_rmse("foundation_mpa0")
    finetuned_rmse = force_rmse("finetuned_3060ti")
    reduction = 100.0 * (foundation_rmse - finetuned_rmse) / foundation_rmse
    ads_min = float(adsorption["adsorption_energy_ev_per_li"].min())
    ads_max = float(adsorption["adsorption_energy_ev_per_li"].max())

    fig = plt.figure(figsize=(12, 4.8), dpi=OUTPUT_DPI, facecolor="white")
    grid = fig.add_gridspec(
        3,
        3,
        height_ratios=[0.16, 0.34, 0.50],
        width_ratios=[1.0, 1.0, 1.0],
        hspace=0.08,
        wspace=0.08,
        left=0.025,
        right=0.975,
        top=0.96,
        bottom=0.05,
    )

    title_ax = fig.add_subplot(grid[0, :])
    title_ax.set_axis_off()
    title_ax.text(
        0.5,
        0.68,
        "Validation-first AI for local lithium energetics",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color=INK,
    )
    title_ax.text(
        0.5,
        0.15,
        "DFT anchors  |  leakage-aware MACE evaluation  |  out-of-domain stress tests",
        ha="center",
        va="center",
        fontsize=12,
        color="#4D5C68",
    )

    structure_ax = fig.add_subplot(grid[1, :])
    structure_ax.set_axis_off()
    structure_ax.imshow(mpimg.imread(STRUCTURE_FIGURE), aspect="auto")

    evidence_ax = fig.add_subplot(grid[2, 0])
    rounded_panel(evidence_ax)
    add_step_title(evidence_ax, "1", "First-principles anchors")
    evidence_ax.text(
        0.08,
        0.60,
        "273",
        transform=evidence_ax.transAxes,
        fontsize=26,
        fontweight="bold",
        color=BLUE,
    )
    evidence_ax.text(
        0.08,
        0.49,
        "spin-polarized VASP frames",
        transform=evidence_ax.transAxes,
        fontsize=11,
        color=INK,
    )
    evidence_ax.text(
        0.08,
        0.34,
        "PBE-D3/dipole adsorption",
        transform=evidence_ax.transAxes,
        fontsize=11,
        fontweight="bold",
        color=INK,
    )
    evidence_ax.text(
        0.08,
        0.20,
        f"{ads_min:.3f} to {ads_max:.3f} eV/Li",
        transform=evidence_ax.transAxes,
        fontsize=16,
        fontweight="bold",
        color=GREEN,
    )
    evidence_ax.text(
        0.08,
        0.045,
        "Relaxations + site/path scans + snapshot DFT",
        transform=evidence_ax.transAxes,
        fontsize=9,
        color="#4D5C68",
    )

    audit_ax = fig.add_subplot(grid[2, 1])
    rounded_panel(audit_ax)
    add_step_title(audit_ax, "2", "Audit before scale-up")
    bar_ax = audit_ax.inset_axes([0.22, 0.40, 0.70, 0.30])
    labels = ["Foundation", "Fine-tuned"]
    values = [foundation_rmse, finetuned_rmse]
    colors = [BLUE, ORANGE]
    y_positions = [0, 1]
    bars = bar_ax.barh(y_positions, values, color=colors, height=0.55)
    bar_ax.set_yticks(y_positions, labels=labels)
    bar_ax.invert_yaxis()
    bar_ax.set_xlim(0, 340)
    bar_ax.tick_params(axis="both", labelsize=8)
    bar_ax.grid(axis="x", color="#D8E0E5", linewidth=0.7)
    bar_ax.spines[["top", "right", "left"]].set_visible(False)
    for bar, value in zip(bars, values, strict=True):
        bar_ax.text(
            value + 6,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=INK,
        )
    audit_ax.text(
        0.22,
        0.21,
        f"{reduction:.1f}% lower, then re-audited",
        transform=audit_ax.transAxes,
        fontsize=11,
        fontweight="bold",
        color=GREEN,
    )
    audit_ax.text(
        0.22,
        0.045,
        "Group-held-out split  |  E0 calibration  |  3 seeds",
        transform=audit_ax.transAxes,
        fontsize=8.5,
        color="#4D5C68",
    )

    gate_ax = fig.add_subplot(grid[2, 2])
    rounded_panel(gate_ax)
    add_step_title(gate_ax, "3", "Gate physical claims")
    gate_ax.text(
        0.07,
        0.69,
        "SUPPORTED",
        transform=gate_ax.transAxes,
        fontsize=10,
        fontweight="bold",
        color=GREEN,
    )
    gate_ax.text(
        0.07,
        0.52,
        "Local adsorption screening\nModel-domain diagnosis",
        transform=gate_ax.transAxes,
        fontsize=12,
        linespacing=1.45,
        color=INK,
    )
    gate_ax.text(
        0.07,
        0.34,
        "WITHHELD",
        transform=gate_ax.transAxes,
        fontsize=10,
        fontweight="bold",
        color=RED,
    )
    gate_ax.text(
        0.07,
        0.17,
        "Unconverged CI-NEB barriers\nDiffusion coefficients",
        transform=gate_ax.transAxes,
        fontsize=12,
        linespacing=1.45,
        color=INK,
    )
    gate_ax.text(
        0.07,
        0.045,
        "9 DFT snapshot tests -> next training-data targets",
        transform=gate_ax.transAxes,
        fontsize=8.5,
        color="#4D5C68",
    )

    for left_ax, right_ax in ((evidence_ax, audit_ax), (audit_ax, gate_ax)):
        left_box = left_ax.get_position()
        right_box = right_ax.get_position()
        fig.add_artist(
            FancyArrowPatch(
                (left_box.x1 + 0.004, (left_box.y0 + left_box.y1) / 2),
                (right_box.x0 - 0.004, (right_box.y0 + right_box.y1) / 2),
                transform=fig.transFigure,
                arrowstyle="-|>",
                mutation_scale=18,
                linewidth=1.8,
                color=BLUE,
                zorder=20,
            )
        )

    png_path = MANUSCRIPT / "graphical_abstract.png"
    pdf_path = MANUSCRIPT / "graphical_abstract.pdf"
    fig.savefig(png_path, dpi=OUTPUT_DPI, facecolor="white")
    fig.savefig(pdf_path, facecolor="white")
    plt.close(fig)
    print(png_path)
    print(pdf_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
