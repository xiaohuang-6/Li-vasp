#!/usr/bin/env python3
"""Create a multi-panel atomistic-structure figure for the manuscript draft."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ase.io import read
from ase.visualize.plot import plot_atoms


CASES = [
    ("(a)", "Pristine graphene + Li", "submission_data/structures/relaxed/A_Perfect.vasp"),
    ("(b)", "Monovacancy + Li", "submission_data/structures/relaxed/B1_Monovacancy.vasp"),
    ("(c)", "Divacancy + Li", "submission_data/structures/relaxed/B2_Divacancy.vasp"),
    ("(d)", "Stone-Wales + Li", "submission_data/structures/relaxed/C_StoneWales.vasp"),
    ("(e)", r"Si$_4$-graphene + Li", "submission_data/structures/relaxed/D_SiGraphene.vasp"),
]

COLORS = {
    "C": "#4c4c4c",
    "Li": "#2ca25f",
    "Si": "#3182bd",
}

RADII = {
    "C": 0.42,
    "Li": 0.78,
    "Si": 0.62,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("manuscript/figures"),
    )
    args = parser.parse_args()
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, len(CASES), figsize=(14.0, 3.2), constrained_layout=True)
    for ax, (panel, title, path) in zip(axes, CASES, strict=True):
        atoms = read(path)
        rotation = "0x,0y,0z"
        colors = [COLORS.get(atom.symbol, "#999999") for atom in atoms]
        radii = [RADII.get(atom.symbol, 0.5) for atom in atoms]
        plot_atoms(atoms, ax=ax, rotation=rotation, colors=colors, radii=radii, show_unit_cell=2)
        ax.set_title(f"{panel} {title}", fontsize=9, pad=3)
        ax.set_axis_off()
        ax.set_aspect("equal")
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", label="C", markerfacecolor=COLORS["C"], markersize=8),
        plt.Line2D([0], [0], marker="o", color="w", label="Li", markerfacecolor=COLORS["Li"], markersize=9),
        plt.Line2D([0], [0], marker="o", color="w", label="Si", markerfacecolor=COLORS["Si"], markersize=9),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.savefig(out_dir / "structure_models.png", dpi=350, bbox_inches="tight")
    fig.savefig(out_dir / "structure_models.pdf", bbox_inches="tight")
    print(out_dir / "structure_models.png")
    print(out_dir / "structure_models.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
