#!/usr/bin/env python3
"""Evaluate MACE models on the completed family-balanced DFT benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from ase.io import read, write
from mace.calculators import MACECalculator
import torch


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
    if len(rows) != 25 or set(row["family"] for row in rows) != EXPECTED_FAMILIES:
        raise ValueError("Balanced benchmark must contain exactly five families and 25 rows")
    if any(count != 5 for count in counts.values()):
        raise ValueError(f"Balanced benchmark must contain five rows per family: {counts}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        default="review_revision/balanced_perturbation_dft_jobs/manifest.csv",
    )
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--model-label", action="append", required=True)
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    parser.add_argument("--dtype", default="float64")
    parser.add_argument(
        "--output-dir",
        default="results/review_revision/balanced_perturbation_mace_eval",
    )
    return parser.parse_args()


def rmse(values: list[float] | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    return float(math.sqrt(np.mean(array * array))) if array.size else float("nan")


def load_converged_outcar(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    if "General timing and accounting informations for this job" not in text:
        raise RuntimeError(f"Incomplete VASP output: {path}")
    oszicar = (path.parent / "OSZICAR").read_text(
        encoding="utf-8", errors="replace"
    )
    iterations = [
        int(value)
        for value in re.findall(
            r"^\s*(?:DAV|RMM|SDA|CGA|CG|DMP|DIA|EIG)\s*:\s*(\d+)",
            oszicar,
            re.MULTILINE,
        )
    ]
    nelm_matches = re.findall(r"\bNELM\s*=\s*(\d+)", text)
    final_iteration = iterations[-1] if iterations else 0
    nelm = int(nelm_matches[-1]) if nelm_matches else 0
    if (
        "aborting loop because EDIFF is reached" not in text
        or final_iteration <= 0
        or nelm <= 0
        or final_iteration >= nelm
    ):
        raise RuntimeError(
            f"Final electronic loop is not converged: {path} "
            f"(last_iter={final_iteration}, NELM={nelm})"
        )
    if any(marker in text for marker in FATAL_MARKERS):
        raise RuntimeError(f"Fatal VASP marker: {path}")
    return read(path, index=-1, format="vasp-out")


def load_cpu_calculator(model_path: str, dtype: str) -> MACECalculator:
    """Force embedded e3nn TorchScript modules onto CPU during deserialization."""
    original_jit_load = torch.jit.load

    def jit_load_cpu(*args, **kwargs):
        kwargs["map_location"] = "cpu"
        return original_jit_load(*args, **kwargs)

    torch.jit.load = jit_load_cpu
    try:
        return MACECalculator(
            model_paths=model_path,
            device="cpu",
            default_dtype=dtype,
        )
    finally:
        torch.jit.load = original_jit_load


def main() -> int:
    args = parse_args()
    if len(args.model) != len(args.model_label):
        raise ValueError("Provide one --model-label for each --model")
    if args.device != "cpu":
        raise ValueError("This project run is restricted to CPU evaluation on the cluster")

    with Path(args.manifest).open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    validate_manifest(manifest)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dft_inputs: list[tuple[dict[str, str], object, str]] = []
    for item in manifest:
        outcar = Path(item["job_dir"]) / "OUTCAR"
        atoms = load_converged_outcar(outcar)
        forces = np.asarray(atoms.get_forces(), dtype=float)
        if forces.shape != (len(atoms), 3) or not np.isfinite(forces).all():
            raise ValueError(f"Unreadable DFT forces: {outcar}")
        outcar_digest = sha256(outcar)
        atoms.info.update(
            {
                "configuration_id": Path(item["job_dir"]).name,
                "family": item["family"],
                "sigma_a": float(item["sigma_a"]),
                "replicate": int(item["replicate"]),
                "seed": int(item["seed"]),
                "source_outcar_sha256": outcar_digest,
                "selection_used_model_predictions": False,
            }
        )
        dft_inputs.append((item, atoms, outcar_digest))
    write(
        output_dir / "balanced_perturbation_dft.extxyz",
        [atoms for _, atoms, _ in dft_inputs],
        format="extxyz",
    )

    frame_rows: list[dict[str, object]] = []
    pooled: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    energy_errors: dict[tuple[str, str], list[float]] = defaultdict(list)
    frame_errors: dict[tuple[str, str], list[float]] = defaultdict(list)
    model_metadata: dict[str, tuple[Path, str]] = {}

    for model_path, model_label in zip(args.model, args.model_label, strict=True):
        if model_label in model_metadata:
            raise ValueError(f"Duplicate model label: {model_label}")
        model_file = Path(model_path)
        if not model_file.is_file():
            raise FileNotFoundError(model_file)
        model_digest = sha256(model_file)
        model_metadata[model_label] = (model_file.resolve(), model_digest)
        calculator = load_cpu_calculator(model_path, args.dtype)
        for item, atoms, outcar_digest in dft_inputs:
            dft_energy = float(atoms.get_potential_energy())
            dft_forces = np.asarray(atoms.get_forces(), dtype=float)
            prediction = atoms.copy()
            prediction.calc = calculator
            mace_energy = float(prediction.get_potential_energy())
            mace_forces = np.asarray(prediction.get_forces(), dtype=float)
            errors = (mace_forces - dft_forces) * 1000.0
            symbols = np.asarray(atoms.get_chemical_symbols())
            family = item["family"]
            frame_rmse = rmse(errors.ravel())
            li_rmse = rmse(errors[symbols == "Li"].ravel())
            substrate_rmse = rmse(errors[symbols != "Li"].ravel())
            energy_error = (mace_energy - dft_energy) * 1000.0 / len(atoms)
            frame_rows.append(
                {
                    "model": model_label,
                    "model_path": str(model_file.resolve()),
                    "model_sha256": model_digest,
                    "family": family,
                    "sigma_a": item["sigma_a"],
                    "replicate": item["replicate"],
                    "seed": item["seed"],
                    "natoms": len(atoms),
                    "energy_error_mev_atom": energy_error,
                    "force_rmse_mev_a": frame_rmse,
                    "li_force_rmse_mev_a": li_rmse,
                    "substrate_force_rmse_mev_a": substrate_rmse,
                    "max_atom_force_error_mev_a": float(
                        np.max(np.linalg.norm(errors, axis=1))
                    ),
                    "configuration_id": Path(item["job_dir"]).name,
                    "source_outcar_sha256": outcar_digest,
                }
            )
            for scope_family in (family, "ALL"):
                pooled[(model_label, scope_family, "all")].extend(errors.ravel())
                pooled[(model_label, scope_family, "li")].extend(errors[symbols == "Li"].ravel())
                pooled[(model_label, scope_family, "substrate")].extend(
                    errors[symbols != "Li"].ravel()
                )
                energy_errors[(model_label, scope_family)].append(energy_error)
                frame_errors[(model_label, scope_family)].append(frame_rmse)

    summary_rows: list[dict[str, object]] = []
    for model_label in args.model_label:
        families = ["ALL"] + sorted({item["family"] for item in manifest})
        for family in families:
            model_file, model_digest = model_metadata[model_label]
            summary_rows.append(
                {
                    "model": model_label,
                    "model_path": str(model_file),
                    "model_sha256": model_digest,
                    "family": family,
                    "n_frames": len(frame_errors[(model_label, family)]),
                    "energy_rmse_mev_atom": rmse(energy_errors[(model_label, family)]),
                    "force_rmse_mev_a_pooled": rmse(pooled[(model_label, family, "all")]),
                    "li_force_rmse_mev_a_pooled": rmse(pooled[(model_label, family, "li")]),
                    "substrate_force_rmse_mev_a_pooled": rmse(
                        pooled[(model_label, family, "substrate")]
                    ),
                    "force_rmse_mev_a_frame_mean": float(
                        np.mean(frame_errors[(model_label, family)])
                    ),
                    "force_rmse_mev_a_frame_max": float(
                        np.max(frame_errors[(model_label, family)])
                    ),
                }
            )

    for name, rows in (("frame_errors.csv", frame_rows), ("summary.csv", summary_rows)):
        with (output_dir / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    lines = [
        "# Balanced Perturbation MACE Force Benchmark",
        "",
        "All model inference in this run used the CPU.",
        "",
        "| Model | Family | n | Force RMSE (meV/angstrom) | Li RMSE | Substrate RMSE |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['model']} | {row['family']} | {row['n_frames']} | "
            f"{row['force_rmse_mev_a_pooled']:.1f} | "
            f"{row['li_force_rmse_mev_a_pooled']:.1f} | "
            f"{row['substrate_force_rmse_mev_a_pooled']:.1f} |"
        )
    (output_dir / "BALANCED_PERTURBATION_MACE_FORCE_BENCHMARK.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(output_dir / "summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
