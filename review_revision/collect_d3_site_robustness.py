#!/usr/bin/env python3
"""Collect the selected-site PBE-D3(BJ)+dipole adsorption energies."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from ase.calculators.singlepoint import SinglePointCalculator
from ase.io import read, write


FATAL_MARKERS = (
    "VERY BAD NEWS",
    "BRMIX: very serious problems",
    "ZBRENT: fatal error",
    "internal error in subroutine PRICEL",
    "Error EDDDAV",
    "Call to ZHEGV failed",
)

EXPECTED_FAMILIES = {
    "A_Perfect",
    "B1_Monovacancy",
    "B2_Divacancy",
    "C_StoneWales",
    "D_SiGraphene",
}

ENERGY_PATTERN = re.compile(
    r"energy\s+without entropy=\s*([-+0-9.Ee]+)\s+"
    r"energy\(sigma->0\)\s*=\s*([-+0-9.Ee]+)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(rows: list[dict[str, str]]) -> None:
    counts = {
        family: sum(row["family"] == family for row in rows)
        for family in EXPECTED_FAMILIES
    }
    if len(rows) != 15 or set(row["family"] for row in rows) != EXPECTED_FAMILIES:
        raise ValueError("D3 site benchmark must contain exactly five families and 15 rows")
    if any(count != 3 for count in counts.values()):
        raise ValueError(f"D3 site benchmark must contain three rows per family: {counts}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest", default="review_revision/d3_site_converged_jobs/manifest.csv"
    )
    parser.add_argument(
        "--output-dir", default="results/review_revision/d3_site_robustness_analysis"
    )
    return parser.parse_args()


def outcar_state(path: Path) -> tuple[bool, bool, bool, float, int, int]:
    if not path.is_file() or path.stat().st_size == 0:
        return False, False, False, float("nan"), 0, 0
    text = path.read_text(encoding="utf-8", errors="replace")
    completed = "General timing and accounting informations for this job" in text
    oszicar = path.parent / "OSZICAR"
    oszicar_text = (
        oszicar.read_text(encoding="utf-8", errors="replace")
        if oszicar.is_file()
        else ""
    )
    iterations = [
        int(value)
        for value in re.findall(
            r"^\s*(?:DAV|RMM|SDA|CGA|CG|DMP|DIA|EIG)\s*:\s*(\d+)",
            oszicar_text,
            re.MULTILINE,
        )
    ]
    nelm_matches = re.findall(r"\bNELM\s*=\s*(\d+)", text)
    final_iteration = iterations[-1] if iterations else 0
    nelm = int(nelm_matches[-1]) if nelm_matches else 0
    converged = (
        "aborting loop because EDIFF is reached" in text
        and final_iteration > 0
        and nelm > 0
        and final_iteration < nelm
    )
    fatal = any(marker in text for marker in FATAL_MARKERS)
    energy = float("nan")
    if completed and converged and not fatal:
        matches = ENERGY_PATTERN.findall(text)
        if matches:
            energy = float(matches[-1][1])
    return completed, converged, fatal, energy, final_iteration, nelm


def read_final_atoms(outcar: Path) -> object:
    """Read a single-point result even when VASP prints E-fermi as stars."""
    text = outcar.read_text(encoding="utf-8", errors="replace")
    atoms = read(outcar.parent / "POSCAR", format="vasp")
    lines = text.splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if "POSITION" in line and "TOTAL-FORCE" in line
    ]
    if not starts:
        raise ValueError(f"no TOTAL-FORCE block in {outcar}")
    force_rows: list[list[float]] = []
    for line in lines[starts[-1] + 2 :]:
        fields = line.split()
        if len(fields) < 6:
            if force_rows:
                break
            continue
        try:
            values = [float(value) for value in fields[:6]]
        except ValueError:
            if force_rows:
                break
            continue
        force_rows.append(values)
        if len(force_rows) == len(atoms):
            break
    if len(force_rows) != len(atoms):
        raise ValueError(
            f"expected {len(atoms)} force rows in {outcar}, found {len(force_rows)}"
        )
    energies = ENERGY_PATTERN.findall(text)
    if not energies:
        raise ValueError(f"no energy(sigma->0) value in {outcar}")
    energy = float(energies[-1][1])
    positions = np.asarray([row[:3] for row in force_rows], dtype=float)
    forces = np.asarray([row[3:6] for row in force_rows], dtype=float)
    if not math.isfinite(energy) or not np.isfinite(positions).all() or not np.isfinite(forces).all():
        raise ValueError(f"non-finite final state in {outcar}")
    atoms.positions = positions
    atoms.calc = SinglePointCalculator(atoms, energy=energy, forces=forces)
    return atoms


def main() -> int:
    args = parse_args()
    with Path(args.manifest).open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    validate_manifest(manifest)

    rows: list[dict[str, object]] = []
    d3_frames = []
    for item in manifest:
        outcar = Path(item["job_dir"]) / "OUTCAR"
        substrate_outcar = Path(item["substrate_job_dir"]) / "OUTCAR"
        li_outcar = Path(item["li_atom_job_dir"]) / "OUTCAR"
        complete, converged, fatal, adsorbed_energy, final_iteration, nelm = outcar_state(
            outcar
        )
        (
            sub_complete,
            sub_converged,
            sub_fatal,
            substrate_energy,
            substrate_final_iteration,
            substrate_nelm,
        ) = outcar_state(substrate_outcar)
        (
            li_complete,
            li_converged,
            li_fatal,
            li_energy,
            li_final_iteration,
            li_nelm,
        ) = outcar_state(li_outcar)
        atoms = None
        forces_readable = False
        substrate_forces_readable = False
        li_atom_forces_readable = False
        parse_error = ""
        substrate_parse_error = ""
        li_atom_parse_error = ""
        if complete and converged and not fatal:
            try:
                atoms = read_final_atoms(outcar)
                forces_readable = True
            except Exception as exc:  # noqa: BLE001
                parse_error = str(exc)
        if sub_complete and sub_converged and not sub_fatal:
            try:
                read_final_atoms(substrate_outcar)
                substrate_forces_readable = True
            except Exception as exc:  # noqa: BLE001
                substrate_parse_error = str(exc)
        if li_complete and li_converged and not li_fatal:
            try:
                read_final_atoms(li_outcar)
                li_atom_forces_readable = True
            except Exception as exc:  # noqa: BLE001
                li_atom_parse_error = str(exc)
        usable = (
            complete
            and converged
            and not fatal
            and forces_readable
            and sub_complete
            and sub_converged
            and not sub_fatal
            and substrate_forces_readable
            and li_complete
            and li_converged
            and not li_fatal
            and li_atom_forces_readable
            and math.isfinite(adsorbed_energy)
            and math.isfinite(substrate_energy)
            and math.isfinite(li_energy)
        )
        adsorption_energy = (
            adsorbed_energy - substrate_energy - li_energy if usable else float("nan")
        )
        if usable:
            assert atoms is not None
            atoms.info.update(
                {
                    "configuration_id": Path(item["job_dir"]).name,
                    "family": item["family"],
                    "site_label": item["label"],
                    "pbe_fixed_site_rank": int(item["pbe_fixed_site_rank"]),
                    "adsorption_energy_ev_per_li": adsorption_energy,
                    "substrate_energy_ev": substrate_energy,
                    "li_atom_energy_ev": li_energy,
                    "source_outcar_sha256": sha256(outcar),
                    "substrate_outcar_sha256": sha256(substrate_outcar),
                    "li_atom_outcar_sha256": sha256(li_outcar),
                    "selection_used_mace_predictions": False,
                }
            )
            d3_frames.append(atoms)
        rows.append(
            {
                **item,
                "completed": complete,
                "outcar_size_bytes": outcar.stat().st_size if outcar.exists() else 0,
                "outcar_mtime_ns": outcar.stat().st_mtime_ns if outcar.exists() else 0,
                "outcar_sha256": sha256(outcar) if outcar.exists() else "",
                "substrate_outcar_size_bytes": (
                    substrate_outcar.stat().st_size if substrate_outcar.exists() else 0
                ),
                "substrate_outcar_sha256": (
                    sha256(substrate_outcar) if substrate_outcar.exists() else ""
                ),
                "li_atom_outcar_size_bytes": (
                    li_outcar.stat().st_size if li_outcar.exists() else 0
                ),
                "li_atom_outcar_sha256": (
                    sha256(li_outcar) if li_outcar.exists() else ""
                ),
                "electronic_converged": converged,
                "final_scf_iteration": final_iteration,
                "nelm": nelm,
                "fatal": fatal,
                "forces_readable": forces_readable,
                "parse_error": parse_error,
                "substrate_forces_readable": substrate_forces_readable,
                "substrate_parse_error": substrate_parse_error,
                "li_atom_forces_readable": li_atom_forces_readable,
                "li_atom_parse_error": li_atom_parse_error,
                "reference_jobs_usable": (
                    sub_complete
                    and sub_converged
                    and not sub_fatal
                    and substrate_forces_readable
                    and li_complete
                    and li_converged
                    and not li_fatal
                    and li_atom_forces_readable
                ),
                "substrate_final_scf_iteration": substrate_final_iteration,
                "substrate_nelm": substrate_nelm,
                "li_atom_final_scf_iteration": li_final_iteration,
                "li_atom_nelm": li_nelm,
                "usable": usable,
                "adsorbed_energy_ev": adsorbed_energy,
                "substrate_energy_ev": substrate_energy,
                "li_atom_energy_ev": li_energy,
                "adsorption_energy_ev_per_li": adsorption_energy,
            }
        )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "d3_site_adsorption_energies.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        if row["usable"]:
            grouped[str(row["family"])].append(row)
    summaries: list[dict[str, object]] = []
    for family in sorted({str(row["family"]) for row in rows}):
        usable_rows = sorted(
            grouped.get(family, []), key=lambda row: float(row["adsorption_energy_ev_per_li"])
        )
        summaries.append(
            {
                "family": family,
                "usable_sites": len(usable_rows),
                "best_site": usable_rows[0]["label"] if usable_rows else "",
                "best_adsorption_energy_ev_per_li": (
                    usable_rows[0]["adsorption_energy_ev_per_li"]
                    if usable_rows
                    else float("nan")
                ),
                "sampled_site_span_ev": (
                    float(usable_rows[-1]["adsorption_energy_ev_per_li"])
                    - float(usable_rows[0]["adsorption_energy_ev_per_li"])
                    if usable_rows
                    else float("nan")
                ),
            }
        )
    with (output_dir / "d3_site_family_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)

    usable_count = sum(bool(row["usable"]) for row in rows)
    extxyz_path = output_dir / "d3_site_structures.extxyz"
    if usable_count == len(rows):
        write(extxyz_path, d3_frames, format="extxyz")
    elif extxyz_path.exists():
        extxyz_path.unlink()
    lines = [
        "# D3 Site Robustness Status",
        "",
        f"- Usable selected-site energies: {usable_count}/{len(rows)}.",
        "- Three sites per family were selected by the preceding PBE fixed-site ranking.",
        "- These are fixed-geometry checks, not relaxed adsorption-site searches.",
        "",
        "| Family | Site | PBE rank | completed | converged | usable | Eads (eV/Li) |",
        "|---|---|---:|---|---|---|---:|",
    ]
    for row in rows:
        energy = row["adsorption_energy_ev_per_li"]
        formatted = f"{energy:.6f}" if row["usable"] else ""
        lines.append(
            f"| {row['family']} | {row['label']} | {row['pbe_fixed_site_rank']} | "
            f"{row['completed']} | {row['electronic_converged']} | {row['usable']} | "
            f"{formatted} |"
        )
    (output_dir / "D3_SITE_ROBUSTNESS_STATUS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(f"Usable: {usable_count}/{len(rows)}")
    return 0 if usable_count == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
