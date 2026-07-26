#!/usr/bin/env python3
"""Build the publication-facing MACE dataset and force-error figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "submission_data" / "results" / "mace_eval_summary.csv"
FIGURE_DIR = ROOT / "manuscript" / "figures"
DATASET_OUTPUT = FIGURE_DIR / "dataset_family_counts.png"
COMPARISON_OUTPUT = FIGURE_DIR / "review_mace_foundation_comparison.png"

FAMILIES = (
    ("A_Perfect", "Pristine"),
    ("B1_Monovacancy", "Mono-\nvacancy"),
    ("B2_Divacancy", "Di-\nvacancy"),
    ("C_StoneWales", "Stone-\nWales"),
    ("D_SiGraphene", "Si$_4$-\ngraphene"),
)
MODELS = (
    ("foundation_mpa0", "Foundation", "#2673A8"),
    ("finetuned_3060ti", "Fine-tuned", "#E07831"),
)
OUTPUT_DPI = 400
INK = "#202A35"
GRID = "#D8E0E5"


def _load_data() -> pd.DataFrame:
    data = pd.read_csv(DATA)
    required = {
        "model_label",
        "split",
        "family",
        "n_frames",
        "force_rmse_mev_a_frame_rms",
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Missing columns in {DATA}: {missing}")
    return data


def _dataset_counts(data: pd.DataFrame) -> list[int]:
    counts: list[int] = []
    for family, _ in FAMILIES:
        rows = data[
            data["model_label"].eq("finetuned_3060ti")
            & data["family"].eq(family)
        ]
        splits = set(rows["split"])
        if splits != {"train", "valid", "test"}:
            raise ValueError(
                f"Expected train/valid/test rows for {family}, found {sorted(splits)}"
            )
        counts.append(int(rows["n_frames"].sum()))
    if sum(counts) != 273:
        raise ValueError(f"Expected 273 frames, found {sum(counts)}")
    return counts


def _test_force_rmse(data: pd.DataFrame, model: str, family: str) -> float:
    rows = data[
        data["model_label"].eq(model)
        & data["split"].eq("test")
        & data["family"].eq(family)
    ]
    if len(rows) != 1:
        raise ValueError(
            f"Expected one test row for model={model}, family={family}; "
            f"found {len(rows)}"
        )
    return float(rows.iloc[0]["force_rmse_mev_a_frame_rms"])


def _style_axis(ax: plt.Axes) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#667783")
    ax.tick_params(axis="both", labelsize=7.5, colors=INK, length=3)


def _save_dataset_figure(data: pd.DataFrame) -> None:
    counts = _dataset_counts(data)
    x = np.arange(len(FAMILIES))

    fig, ax = plt.subplots(figsize=(4.0, 2.0), dpi=OUTPUT_DPI)
    fig.subplots_adjust(left=0.14, right=0.99, top=0.79, bottom=0.28)
    bars = ax.bar(x, counts, width=0.68, color="#5B7FAE")

    _style_axis(ax)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Frames", fontsize=8.5, color=INK)
    ax.set_xticks(x, [label for _, label in FAMILIES])
    ax.bar_label(bars, padding=2, fontsize=7.2, color=INK)

    fig.text(
        0.14,
        0.94,
        "DFT-labeled frames by structural family",
        ha="left",
        va="top",
        fontsize=9.3,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.14,
        0.825,
        "273 frames total",
        ha="left",
        va="top",
        fontsize=7.4,
        color="#4D5C68",
    )
    fig.savefig(
        DATASET_OUTPUT,
        dpi=OUTPUT_DPI,
        facecolor="white",
        metadata={"Software": "Matplotlib"},
    )
    plt.close(fig)


def _save_comparison_figure(data: pd.DataFrame) -> None:
    x = np.arange(len(FAMILIES))
    width = 0.36

    fig, ax = plt.subplots(figsize=(4.0, 2.0), dpi=OUTPUT_DPI)
    fig.subplots_adjust(left=0.17, right=0.99, top=0.75, bottom=0.28)

    for index, (model, label, color) in enumerate(MODELS):
        values = [
            _test_force_rmse(data, model, family)
            for family, _ in FAMILIES
        ]
        offset = (index - 0.5) * width
        bars = ax.bar(
            x + offset,
            values,
            width=width,
            label=label,
            color=color,
        )
        ax.bar_label(
            bars,
            labels=[f"{value:.1f}" for value in values],
            padding=1.5,
            fontsize=6.4,
            color=INK,
        )

    _style_axis(ax)
    ax.set_ylim(0, 420)
    ax.set_ylabel(
        r"Force RMSE (meV $\mathrm{\AA}^{-1}$)",
        fontsize=8.2,
        color=INK,
    )
    ax.set_xticks(x, [label for _, label in FAMILIES])
    ax.legend(
        loc="upper right",
        frameon=False,
        fontsize=7.0,
        handlelength=1.4,
        borderaxespad=0.2,
    )

    fig.text(
        0.17,
        0.94,
        "Initial same-workflow test force RMSE",
        ha="left",
        va="top",
        fontsize=9.3,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.17,
        0.825,
        "Original diagnostic split; not a transferability test",
        ha="left",
        va="top",
        fontsize=7.4,
        color="#4D5C68",
    )
    fig.savefig(
        COMPARISON_OUTPUT,
        dpi=OUTPUT_DPI,
        facecolor="white",
        metadata={"Software": "Matplotlib"},
    )
    plt.close(fig)


def main() -> int:
    data = _load_data()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    _save_dataset_figure(data)
    _save_comparison_figure(data)
    print(f"Wrote {DATASET_OUTPUT}")
    print(f"Wrote {COMPARISON_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
