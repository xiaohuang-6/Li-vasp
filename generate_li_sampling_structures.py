#!/usr/bin/env python3
"""Generate Li adsorption and path-sampling structures from optimized slabs.

The generated POSCAR files are intended for fixed-geometry VASP single-point
energy/force labels. Existing Li atoms are removed from each optimized input,
then one Li atom is placed at reproducible adsorption/path positions.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from ase import Atom, Atoms
from ase.io import read, write


DEFAULT_CASES = (
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
)


@dataclass(frozen=True)
class Site:
    label: str
    frac_xy: np.ndarray
    z: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Li adsorption/path structures for VASP SP labels."
    )
    parser.add_argument("--input-root", default="dft_outputs")
    parser.add_argument("--output-dir", default="structures/li_sampling")
    parser.add_argument("--cases", nargs="+", default=list(DEFAULT_CASES))
    parser.add_argument(
        "--li-height",
        type=float,
        default=1.7,
        help="Li height above graphene C mean z for graphene sites.",
    )
    parser.add_argument(
        "--si-li-height",
        type=float,
        default=1.9,
        help="Li height above selected Si sites for Si-graphene structures.",
    )
    parser.add_argument(
        "--path-images",
        type=int,
        default=5,
        help="Interior interpolation images per selected site pair.",
    )
    parser.add_argument(
        "--min-li-distance",
        type=float,
        default=1.35,
        help="Reject generated structures with Li closer than this to any atom.",
    )
    parser.add_argument("--summary", default=None)
    return parser.parse_args()


def clean_label(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_+-]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def frac_delta(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    delta = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    return delta - np.round(delta)


def frac_distance_xy(a: np.ndarray, b: np.ndarray, cell: np.ndarray) -> float:
    delta = frac_delta(a[:2], b[:2])
    cart = delta[0] * cell[0] + delta[1] * cell[1]
    return float(np.linalg.norm(cart[:2]))


def frac_midpoint(anchor: np.ndarray, other: np.ndarray) -> np.ndarray:
    return (anchor[:2] + 0.5 * frac_delta(other[:2], anchor[:2])) % 1.0


def frac_average(anchor: np.ndarray, points: list[np.ndarray]) -> np.ndarray:
    if not points:
        return anchor[:2] % 1.0
    deltas = [frac_delta(point[:2], anchor[:2]) for point in points]
    return (anchor[:2] + np.mean(deltas, axis=0)) % 1.0


def cart_from_frac_xy(atoms: Atoms, frac_xy: np.ndarray, z: float) -> np.ndarray:
    cell = atoms.cell.array
    pos = frac_xy[0] * cell[0] + frac_xy[1] * cell[1]
    return np.array([pos[0], pos[1], z], dtype=float)


def remove_li(atoms: Atoms) -> tuple[Atoms, np.ndarray | None]:
    symbols = atoms.get_chemical_symbols()
    li_indices = [idx for idx, symbol in enumerate(symbols) if symbol == "Li"]
    prior_li_frac = None
    if li_indices:
        prior_li_frac = atoms.get_scaled_positions(wrap=True)[li_indices[0], :2]
    keep = [idx for idx, symbol in enumerate(symbols) if symbol != "Li"]
    substrate = atoms[keep]
    substrate.pbc = atoms.pbc
    return substrate, prior_li_frac


def nearest_indices_by_frac(
    atoms: Atoms, candidate_indices: list[int], target_frac_xy: np.ndarray
) -> list[int]:
    scaled = atoms.get_scaled_positions(wrap=True)
    cell = atoms.cell.array
    return sorted(
        candidate_indices,
        key=lambda idx: frac_distance_xy(scaled[idx], target_frac_xy, cell),
    )


def unique_sites(sites: list[Site], atoms: Atoms, min_sep: float = 0.35) -> list[Site]:
    unique: list[Site] = []
    for site in sites:
        duplicate = False
        for existing in unique:
            if (
                frac_distance_xy(
                    np.r_[site.frac_xy, 0.0],
                    np.r_[existing.frac_xy, 0.0],
                    atoms.cell.array,
                )
                < min_sep
                and abs(site.z - existing.z) < 0.25
            ):
                duplicate = True
                break
        if not duplicate:
            unique.append(site)
    return unique


def graphene_sites(substrate: Atoms, prior_li_frac: np.ndarray | None, height: float) -> list[Site]:
    symbols = substrate.get_chemical_symbols()
    c_indices = [idx for idx, symbol in enumerate(symbols) if symbol == "C"]
    if not c_indices:
        raise ValueError("No C atoms found; cannot define graphene adsorption sites")

    scaled = substrate.get_scaled_positions(wrap=True)
    target = prior_li_frac if prior_li_frac is not None else np.array([0.5, 0.5])
    nearest_c = nearest_indices_by_frac(substrate, c_indices, target)
    central = nearest_c[0]
    neighbors = nearest_c[1:4]
    graph_z = float(np.mean(substrate.positions[c_indices, 2]))
    z = graph_z + height

    sites = [
        Site("prior_li_xy", np.asarray(target, dtype=float) % 1.0, z),
        Site("cell_center", np.array([0.5, 0.5]), z),
        Site("top_central_C", scaled[central, :2], z),
    ]
    if neighbors:
        sites.append(Site("bridge_C_C", frac_midpoint(scaled[central], scaled[neighbors[0]]), z))
    if len(neighbors) >= 2:
        sites.append(
            Site(
                "hollow_C3",
                frac_average(scaled[central], [scaled[central], scaled[neighbors[0]], scaled[neighbors[1]]]),
                z,
            )
        )
    if len(nearest_c) >= 6:
        sites.append(Site("top_offset_C", scaled[nearest_c[5], :2], z))

    return unique_sites(sites, substrate)


def si_graphene_sites(substrate: Atoms, prior_li_frac: np.ndarray | None, height: float, si_height: float) -> list[Site]:
    sites = graphene_sites(substrate, prior_li_frac, height)
    symbols = substrate.get_chemical_symbols()
    si_indices = [idx for idx, symbol in enumerate(symbols) if symbol == "Si"]
    c_indices = [idx for idx, symbol in enumerate(symbols) if symbol == "C"]
    if not si_indices:
        return sites

    scaled = substrate.get_scaled_positions(wrap=True)
    si_top = max(si_indices, key=lambda idx: substrate.positions[idx, 2])
    si_centroid_frac = frac_average(scaled[si_top], [scaled[idx] for idx in si_indices])
    si_top_z = float(substrate.positions[si_top, 2] + si_height)
    sites.append(Site("top_highest_Si", scaled[si_top, :2], si_top_z))
    sites.append(Site("si_cluster_centroid", si_centroid_frac, si_top_z))

    if c_indices:
        nearest_c = nearest_indices_by_frac(substrate, c_indices, scaled[si_top, :2])[0]
        interface_xy = frac_midpoint(scaled[si_top], scaled[nearest_c])
        interface_z = float(0.5 * (substrate.positions[si_top, 2] + substrate.positions[nearest_c, 2]) + height)
        sites.append(Site("si_graphene_interface", interface_xy, interface_z))

    return unique_sites(sites, substrate)


def make_structure(substrate: Atoms, site: Site) -> Atoms:
    atoms = substrate.copy()
    atoms.append(Atom("Li", position=cart_from_frac_xy(substrate, site.frac_xy, site.z)))
    atoms.pbc = (True, True, True)
    return atoms


def li_min_distance(atoms: Atoms) -> float:
    symbols = atoms.get_chemical_symbols()
    li_index = max(idx for idx, symbol in enumerate(symbols) if symbol == "Li")
    distances = atoms.get_distances(li_index, [idx for idx in range(len(atoms)) if idx != li_index], mic=True)
    return float(np.min(distances))


def write_structure(output_dir: Path, case: str, label: str, atoms: Atoms) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"POSCAR_SP_{case}_{clean_label(label)}.vasp"
    path = output_dir / filename
    write(path, atoms, format="vasp", vasp5=True, direct=True, sort=True)
    return {
        "file": str(path),
        "case": case,
        "label": label,
        "formula": atoms.get_chemical_formula(),
        "natoms": len(atoms),
        "li_min_distance": li_min_distance(atoms),
    }


def path_sites(sites: list[Site], images: int) -> list[Site]:
    if images <= 0 or len(sites) < 2:
        return []
    pairs = [(0, min(3, len(sites) - 1))]
    if len(sites) > 4:
        pairs.append((2, 4))

    generated: list[Site] = []
    for pair_index, (start_idx, end_idx) in enumerate(pairs, start=1):
        start = sites[start_idx]
        end = sites[end_idx]
        delta_xy = frac_delta(end.frac_xy, start.frac_xy)
        dz = end.z - start.z
        for image in range(1, images + 1):
            t = image / float(images + 1)
            frac_xy = (start.frac_xy + t * delta_xy) % 1.0
            z = float(start.z + t * dz)
            generated.append(
                Site(
                    f"path{pair_index:02d}_{start.label}_to_{end.label}_img{image:02d}",
                    frac_xy,
                    z,
                )
            )
    return generated


def main() -> int:
    args = parse_args()
    input_root = Path(args.input_root)
    output_dir = Path(args.output_dir)
    records: list[dict[str, object]] = []
    skipped: list[dict[str, object]] = []

    for case in args.cases:
        input_path = input_root / case / "CONTCAR"
        if not input_path.exists():
            skipped.append({"case": case, "reason": f"missing {input_path}"})
            continue

        atoms = read(input_path)
        substrate, prior_li_frac = remove_li(atoms)
        if "Si" in substrate.get_chemical_symbols():
            sites = si_graphene_sites(substrate, prior_li_frac, args.li_height, args.si_li_height)
        else:
            sites = graphene_sites(substrate, prior_li_frac, args.li_height)
        all_sites = sites + path_sites(sites, args.path_images)

        for site in all_sites:
            generated = make_structure(substrate, site)
            min_dist = li_min_distance(generated)
            if min_dist < args.min_li_distance:
                skipped.append(
                    {
                        "case": case,
                        "label": site.label,
                        "reason": f"Li min distance {min_dist:.3f} < {args.min_li_distance:.3f}",
                    }
                )
                continue
            records.append(write_structure(output_dir, case, site.label, generated))

    summary_path = Path(args.summary) if args.summary else output_dir / "li_sampling_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "input_root": str(input_root),
        "output_dir": str(output_dir),
        "n_structures": len(records),
        "n_skipped": len(skipped),
        "records": records,
        "skipped": skipped,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} POSCAR files under {output_dir}")
    print(f"Skipped {len(skipped)} candidate sites")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
