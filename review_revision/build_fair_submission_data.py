#!/usr/bin/env python3
"""Build and verify a compact, path-sanitized submission data package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT
OUTPUT = ROOT / "submission_data"

COPY_FILES = {
    "dft_outputs/A_Perfect/CONTCAR": "structures/relaxed/A_Perfect.vasp",
    "dft_outputs/B1_Monovacancy/CONTCAR": "structures/relaxed/B1_Monovacancy.vasp",
    "dft_outputs/B2_Divacancy/CONTCAR": "structures/relaxed/B2_Divacancy.vasp",
    "dft_outputs/C_StoneWales/CONTCAR": "structures/relaxed/C_StoneWales.vasp",
    "dft_outputs/D_SiGraphene/CONTCAR": "structures/relaxed/D_SiGraphene.vasp",
    "data/mace_datasets/li_mace_train.extxyz": "datasets/original_split/train.extxyz",
    "data/mace_datasets/li_mace_valid.extxyz": "datasets/original_split/valid.extxyz",
    "data/mace_datasets/li_mace_test.extxyz": "datasets/original_split/test.extxyz",
    "data/mace_datasets/li_mace_dataset_report.json": "datasets/original_split/report.json",
    "data/mace_datasets_grouped/li_mace_grouped_train.extxyz": "datasets/grouped_split/train.extxyz",
    "data/mace_datasets_grouped/li_mace_grouped_valid.extxyz": "datasets/grouped_split/valid.extxyz",
    "data/mace_datasets_grouped/li_mace_grouped_test.extxyz": "datasets/grouped_split/test.extxyz",
    "data/mace_datasets_grouped/li_mace_grouped_dataset_report.json": "datasets/grouped_split/report.json",
    "results/review_revision/gpu_analysis_20260725_0116/mace_eval_summary.csv": "results/mace_eval_summary.csv",
    "results/review_revision/gpu_analysis_20260725_0116/committee_summary.csv": "results/committee_summary.csv",
    "results/review_revision/gpu_analysis/review_md_runs.csv": "results/initial_md_runs.csv",
    "results/review_revision/gpu_analysis/review_md_aggregate.csv": "results/initial_md_aggregate.csv",
    "results/review_revision/gpu_analysis_20260725_0116/review_md_runs.csv": "results/production_md_runs.csv",
    "results/review_revision/gpu_analysis_20260725_0116/review_md_aggregate.csv": "results/production_md_aggregate.csv",
    "results/review_revision/gpu_analysis_20260725_0116/review_md_msd_traces_sampled.csv":
        "results/review_md_msd_traces_sampled.csv",
    "review_revision/SNAPSHOT_DFT_EVIDENCE.csv": "results/initial_snapshot_dft_evidence.csv",
    "results/review_revision/high_displacement_mace_eval_strict/foundation_mpa0_snapshot_force_errors.csv": "results/foundation_snapshot_force_errors.csv",
    "results/review_revision/high_displacement_mace_eval_strict/foundation_mpa0_snapshot_force_summary.csv": "results/foundation_snapshot_force_summary.csv",
    "results/review_revision/high_displacement_mace_eval_strict/grouped_e0_snapshot_force_errors.csv": "results/grouped_e0_snapshot_force_errors.csv",
    "results/review_revision/high_displacement_mace_eval_strict/grouped_e0_snapshot_force_summary.csv": "results/grouped_e0_snapshot_force_summary.csv",
    "results/review_revision/high_displacement_mace_eval_strict/high_displacement_dft.extxyz":
        "results/high_displacement_dft.extxyz",
    "results/two_day_rush/path_barriers.csv": "results/fixed_path_descriptors.csv",
    "results/two_day_rush/path_profiles.csv": "results/fixed_path_profiles.csv",
    "results/two_day_rush/site_energy_rankings.csv": "results/fixed_site_energies.csv",
    "results/two_day_rush/training_curve.csv": "results/training_curve.csv",
    "results/review_revision/training_label_scf_audit.csv":
        "results/training_label_scf_audit.csv",
    "review_revision/balanced_perturbation_dft_jobs/manifest.csv":
        "design/balanced_perturbation_manifest.csv",
    "review_revision/d3_site_converged_jobs/manifest.csv":
        "design/d3_site_manifest.csv",
    "review_revision/high_displacement_converged_jobs/combined_manifest.csv":
        "design/high_displacement_manifest.csv",
    "results/review_revision/balanced_perturbation_dft_analysis/balanced_perturbation_dft_status.csv":
        "results/balanced_perturbation_dft_status.csv",
    "results/review_revision/balanced_perturbation_mace_eval/balanced_perturbation_dft.extxyz":
        "results/balanced_perturbation_dft.extxyz",
    "results/review_revision/balanced_perturbation_mace_eval/frame_errors.csv":
        "results/balanced_perturbation_force_errors.csv",
    "results/review_revision/balanced_perturbation_mace_eval/summary.csv":
        "results/balanced_perturbation_force_summary.csv",
    "results/review_revision/d3_site_robustness_analysis/d3_site_adsorption_energies.csv":
        "results/d3_site_adsorption_energies.csv",
    "results/review_revision/d3_site_robustness_analysis/d3_site_family_summary.csv":
        "results/d3_site_family_summary.csv",
    "results/review_revision/d3_site_robustness_analysis/d3_site_structures.extxyz":
        "results/d3_site_structures.extxyz",
}

TEXT_FILES = {
    "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/logs/agent_grouped_e0_finetune.log": "logs/grouped_e0_training_audit.log",
    "review_revision/balanced_perturbation_dft_jobs/DESIGN.md":
        "design/BALANCED_PERTURBATION_DESIGN.md",
    "review_revision/d3_site_converged_jobs/DESIGN.md":
        "design/D3_SITE_DESIGN.md",
    "review_revision/high_displacement_converged_jobs/DESIGN.md":
        "design/HIGH_DISPLACEMENT_SCF_DESIGN.md",
}

PRODUCTION_SNAPSHOT_SOURCE = (
    "results/review_revision/production_md_snapshot_dft_analysis/"
    "md_snapshot_dft_results.csv"
)
PRODUCTION_SNAPSHOT_TARGET = "results/extended_snapshot_dft_evidence.csv"
PRODUCTION_SNAPSHOT_FIELDS = (
    "structure",
    "model_context",
    "velocity_seed",
    "step",
    "time_ps",
    "msd_xy_a2",
    "natoms",
    "completed",
    "electronic_converged_marker",
    "final_scf_iteration",
    "nelm",
    "fatal_error",
    "usable_dft_energy_ev",
    "energy_source",
    "outcar_size_bytes",
    "outcar_sha256",
)

FORBIDDEN_NAMES = {
    "POTCAR",
    "OUTCAR",
    "WAVECAR",
    "CHGCAR",
    "vasprun.xml",
}

PRIVATE_PATH_PATTERN = re.compile(r"/(?:home|Users)/[^,\s\"']+")

EXPECTED_MODEL_HASHES = {
    "models/li_mace_v1_3060ti.model":
        "2b5227ce65cc392bcba62cbdafd345a1be1fd31ebb0ca295e364f53d54b919d1",
    "models/li_mace_review_seed20260427.model":
        "0811bed40f55755393b86c53edc0ec500cb8ad76d46b8393aad214f4a800d0b3",
    "models/li_mace_review_seed20260428.model":
        "43102d78a25b8e8904db1cfda24a8e4105276980d65a4d1bcc9587de77f8d3e4",
    "models/li_mace_review_seed20260429.model":
        "ae4fdce775236e5f9689387257402136877c7543e3cd1b71efd13750e6e9f7c1",
    "models/li_mace_grouped_e0_seed20260430.model":
        "2abd951d5c8dcf13925eb6e5d0974e4790373d288b35d711d24787cd0e629dcf",
}

RELAXED_FAMILIES = (
    ("A_Perfect", "Pristine graphene"),
    ("B1_Monovacancy", "Monovacancy graphene"),
    ("B2_Divacancy", "Divacancy graphene"),
    ("C_StoneWales", "Stone--Wales graphene"),
    ("D_SiGraphene", "Si4--graphene motif"),
)


def sanitize_text(value: str) -> str:
    value = value.replace(f"{ROOT}/", "")
    value = value.replace(f"{EVIDENCE_ROOT}/", "")
    value = re.sub(
        r"/home/duke/work/local_5080_referee_followup_pack_[^/]+/",
        "local_5080_referee_followup_pack/",
        value,
    )
    value = PRIVATE_PATH_PATTERN.sub("<external_path>", value)
    return value


def copy_csv(source: Path, target: Path) -> None:
    with source.open(newline="", encoding="utf-8") as source_handle:
        reader = csv.reader(source_handle)
        rows = [[sanitize_text(value) for value in row] for row in reader]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as target_handle:
        writer = csv.writer(target_handle, lineterminator="\n")
        writer.writerows(rows)


def copy_path_descriptors(source: Path, target: Path) -> None:
    """Export historical path data without migration-barrier terminology."""
    with source.open(newline="", encoding="utf-8") as source_handle:
        rows = list(csv.DictReader(source_handle))
    fieldnames = (
        "family",
        "path_id",
        "path_start",
        "path_end",
        "n_points",
        "start_energy_ev",
        "end_energy_ev",
        "max_minus_start_ev",
        "path_span_ev",
        "delta_e_end_minus_start_ev",
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as target_handle:
        writer = csv.DictWriter(target_handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "family": sanitize_text(row["family"]),
                    "path_id": sanitize_text(row["path_id"]),
                    "path_start": sanitize_text(row["path_start"]),
                    "path_end": sanitize_text(row["path_end"]),
                    "n_points": sanitize_text(row["n_points"]),
                    "start_energy_ev": sanitize_text(row["start_energy_ev"]),
                    "end_energy_ev": sanitize_text(row["end_energy_ev"]),
                    "max_minus_start_ev": sanitize_text(row["barrier_from_start_ev"]),
                    "path_span_ev": sanitize_text(row["barrier_from_path_min_ev"]),
                    "delta_e_end_minus_start_ev": sanitize_text(
                        row["delta_e_end_minus_start_ev"]
                    ),
                }
            )


def copy_sanitized_text(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    sanitized = sanitize_text(source.read_text(encoding="utf-8", errors="replace"))
    normalized = "\n".join(line.rstrip() for line in sanitized.splitlines()) + "\n"
    target.write_text(
        normalized,
        encoding="utf-8",
    )


def copy_converged_production_snapshots(source: Path, target: Path) -> None:
    with source.open(newline="", encoding="utf-8") as source_handle:
        rows = [
            row
            for row in csv.DictReader(source_handle)
            if row["completed"] == "True"
            and row["electronic_converged_marker"] == "True"
            and int(row["final_scf_iteration"]) < int(row["nelm"])
            and row["fatal_error"] == "False"
            and row["usable_dft_energy_ev"]
        ]
    if len(rows) != 7:
        raise ValueError(
            "expected exactly seven converged extended-trajectory snapshot rows, "
            f"found {len(rows)}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as target_handle:
        writer = csv.DictWriter(
            target_handle,
            fieldnames=PRODUCTION_SNAPSHOT_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            case = row["case"]
            if case == "D_SiGraphene":
                model_context = "reference_finetuned_model"
            elif case == "li_mace_review_seed20260429_D_SiGraphene":
                model_context = "committee_model_seed20260429"
            else:
                raise ValueError(f"unexpected production snapshot case: {case}")
            outcar = Path(row["job_dir"]) / "OUTCAR"
            if not outcar.is_file():
                raise FileNotFoundError(outcar)
            writer.writerow(
                {
                    "structure": sanitize_text(row["structure"]),
                    "model_context": model_context,
                    "velocity_seed": sanitize_text(row["seed"]),
                    "step": sanitize_text(row["step"]),
                    "time_ps": sanitize_text(row["time_ps"]),
                    "msd_xy_a2": sanitize_text(row["msd_xy_a2"]),
                    "natoms": sanitize_text(row["natoms"]),
                    "completed": sanitize_text(row["completed"]),
                    "electronic_converged_marker": sanitize_text(
                        row["electronic_converged_marker"]
                    ),
                    "final_scf_iteration": sanitize_text(row["final_scf_iteration"]),
                    "nelm": sanitize_text(row["nelm"]),
                    "fatal_error": sanitize_text(row["fatal_error"]),
                    "usable_dft_energy_ev": sanitize_text(
                        row["usable_dft_energy_ev"]
                    ),
                    "energy_source": sanitize_text(row["energy_source"]),
                    "outcar_size_bytes": outcar.stat().st_size,
                    "outcar_sha256": digest(outcar),
                }
            )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def relaxed_structure_row(family: str, label: str) -> dict[str, object]:
    outcar = EVIDENCE_ROOT / "dft_outputs" / family / "OUTCAR"
    if not outcar.is_file():
        raise FileNotFoundError(outcar)
    text = outcar.read_text(encoding="utf-8", errors="replace")
    moment_matches = re.findall(
        r"number of electron\s+[+-]?[0-9.]+\s+magnetization\s+([+-]?[0-9.]+)",
        text,
    )
    if not moment_matches:
        raise ValueError(f"final magnetic moment not found in {outcar}")

    nions_match = re.search(r"\bNIONS\s*=\s*(\d+)", text)
    if nions_match is None:
        raise ValueError(f"NIONS not found in {outcar}")
    nions = int(nions_match.group(1))
    lines = text.splitlines()
    force_starts = [
        index
        for index, line in enumerate(lines)
        if "POSITION" in line and "TOTAL-FORCE" in line
    ]
    if not force_starts:
        raise ValueError(f"no TOTAL-FORCE blocks in {outcar}")
    force_norms: list[float] = []
    for line in lines[force_starts[-1] + 2 :]:
        fields = line.split()
        if len(fields) < 6:
            if force_norms:
                break
            continue
        try:
            force = [float(value) for value in fields[3:6]]
        except ValueError:
            if force_norms:
                break
            continue
        force_norms.append(math.sqrt(sum(value * value for value in force)))
        if len(force_norms) == nions:
            break
    if len(force_norms) != nions:
        raise ValueError(
            f"expected {nions} final force rows in {outcar}, found {len(force_norms)}"
        )
    ionic_converged = (
        "reached required accuracy - stopping structural energy minimisation" in text
    )
    max_force = max(force_norms)
    if not ionic_converged or max_force >= 0.02:
        raise ValueError(
            f"relaxed structure did not pass ionic gate for {family}: "
            f"converged={ionic_converged}, max_force={max_force}"
        )
    moment = float(moment_matches[-1])
    return {
        "family": family,
        "label": label,
        "natoms": nions,
        "ionic_steps": len(force_starts),
        "ionic_converged": ionic_converged,
        "final_max_force_ev_a": max_force,
        "final_total_moment_mu_b": 0.0 if abs(moment) < 0.0005 else moment,
        "outcar_size_bytes": outcar.stat().st_size,
        "outcar_sha256": digest(outcar),
    }


def write_relaxed_structure_summary() -> None:
    rows = [
        relaxed_structure_row(family, label)
        for family, label in RELAXED_FAMILIES
    ]
    target = OUTPUT / "results/relaxed_structure_dft_summary.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def package_files() -> list[Path]:
    return sorted(
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "MANIFEST.sha256"
    )


def rows_have_fields(rows: list[dict[str, str]], fields: set[str]) -> bool:
    """Return whether a non-empty CSV table contains every required column."""
    return bool(rows) and fields.issubset(rows[0])


def write_manifest() -> None:
    lines = [
        f"{digest(path)}  {path.relative_to(OUTPUT).as_posix()}"
        for path in package_files()
    ]
    (OUTPUT / "MANIFEST.sha256").write_text(
        "\n".join(lines) + "\n",
        encoding="ascii",
    )


def build() -> None:
    stale_anchor = OUTPUT / "results/adsorption_energies.csv"
    if stale_anchor.exists():
        stale_anchor.unlink()
    for source_name, target_name in COPY_FILES.items():
        source = EVIDENCE_ROOT / source_name
        target = OUTPUT / target_name
        if not source.exists():
            raise FileNotFoundError(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target_name == "results/fixed_path_descriptors.csv":
            copy_path_descriptors(source, target)
        elif source.suffix == ".csv":
            copy_csv(source, target)
        else:
            shutil.copy2(source, target)

    for source_name, target_name in TEXT_FILES.items():
        source = EVIDENCE_ROOT / source_name
        target = OUTPUT / target_name
        if not source.exists():
            raise FileNotFoundError(source)
        copy_sanitized_text(source, target)

    copy_converged_production_snapshots(
        EVIDENCE_ROOT / PRODUCTION_SNAPSHOT_SOURCE,
        OUTPUT / PRODUCTION_SNAPSHOT_TARGET,
    )
    write_relaxed_structure_summary()

    write_manifest()


def verify() -> list[str]:
    errors: list[str] = []
    manifest = OUTPUT / "MANIFEST.sha256"
    if not manifest.exists():
        return [f"missing manifest: {manifest}"]

    manifest_rows: dict[str, str] = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            errors.append(f"malformed manifest line: {line}")
            continue
        manifest_rows[relative] = expected

    actual_files = {
        path.relative_to(OUTPUT).as_posix(): path for path in package_files()
    }
    required_files = {
        *EXPECTED_MODEL_HASHES,
        "models/README.md",
        "design/BALANCED_PERTURBATION_DESIGN.md",
        "design/D3_SITE_DESIGN.md",
        "design/balanced_perturbation_manifest.csv",
        "design/d3_site_manifest.csv",
        "design/HIGH_DISPLACEMENT_SCF_DESIGN.md",
        "design/high_displacement_manifest.csv",
        "results/balanced_perturbation_dft.extxyz",
        "results/balanced_perturbation_dft_status.csv",
        "results/balanced_perturbation_force_errors.csv",
        "results/balanced_perturbation_force_summary.csv",
        "results/d3_site_adsorption_energies.csv",
        "results/d3_site_family_summary.csv",
        "results/d3_site_structures.extxyz",
        "results/extended_snapshot_dft_evidence.csv",
        "results/foundation_snapshot_force_errors.csv",
        "results/foundation_snapshot_force_summary.csv",
        "results/grouped_e0_snapshot_force_errors.csv",
        "results/grouped_e0_snapshot_force_summary.csv",
        "results/high_displacement_dft.extxyz",
        "results/initial_snapshot_dft_evidence.csv",
        "results/initial_md_aggregate.csv",
        "results/initial_md_runs.csv",
        "results/production_md_aggregate.csv",
        "results/production_md_runs.csv",
        "results/review_md_msd_traces_sampled.csv",
        "results/relaxed_structure_dft_summary.csv",
        "results/training_label_scf_audit.csv",
        "structures/relaxed/A_Perfect.vasp",
        "structures/relaxed/B1_Monovacancy.vasp",
        "structures/relaxed/B2_Divacancy.vasp",
        "structures/relaxed/C_StoneWales.vasp",
        "structures/relaxed/D_SiGraphene.vasp",
    }
    missing_required = sorted(required_files - set(actual_files))
    if missing_required:
        errors.append(f"required result files missing: {missing_required}")
    if set(manifest_rows) != set(actual_files):
        missing = sorted(set(manifest_rows) - set(actual_files))
        extra = sorted(set(actual_files) - set(manifest_rows))
        if missing:
            errors.append(f"manifest files missing: {missing}")
        if extra:
            errors.append(f"manifest files unlisted: {extra}")

    for relative, path in actual_files.items():
        if path.name in FORBIDDEN_NAMES:
            errors.append(f"forbidden licensed/heavy file: {relative}")
        expected = manifest_rows.get(relative)
        if expected is not None and digest(path) != expected:
            errors.append(f"hash mismatch: {relative}")
        if path.suffix.lower() in {".csv", ".json", ".md", ".txt", ".log", ".extxyz"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            match = PRIVATE_PATH_PATTERN.search(text)
            if match:
                errors.append(
                    f"private absolute path in {relative}: {match.group(0)}"
                )
            if any(line != line.rstrip() for line in text.splitlines()):
                errors.append(f"trailing whitespace in {relative}")

    for relative, expected in EXPECTED_MODEL_HASHES.items():
        path = OUTPUT / relative
        if path.is_file() and digest(path) != expected:
            errors.append(f"unexpected model checkpoint hash: {relative}")

    expected_extxyz = {
        "datasets/original_split/train.extxyz": 211,
        "datasets/original_split/valid.extxyz": 31,
        "datasets/original_split/test.extxyz": 31,
        "datasets/grouped_split/train.extxyz": 263,
        "datasets/grouped_split/valid.extxyz": 5,
        "datasets/grouped_split/test.extxyz": 5,
        "results/balanced_perturbation_dft.extxyz": 25,
        "results/d3_site_structures.extxyz": 15,
        "results/high_displacement_dft.extxyz": 9,
    }
    for relative, expected_frames in expected_extxyz.items():
        path = OUTPUT / relative
        if not path.exists():
            errors.append(f"missing dataset split: {relative}")
            continue
        frame_headers = sum(
            1
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.isdigit()
        )
        if frame_headers != expected_frames:
            errors.append(
                f"frame count mismatch for {relative}: "
                f"{frame_headers} != {expected_frames}"
            )

    initial_md_path = OUTPUT / "results/initial_md_runs.csv"
    if initial_md_path.exists():
        with initial_md_path.open(newline="", encoding="utf-8") as handle:
            initial_md_rows = list(csv.DictReader(handle))
        initial_md_fields = {
            "completed_100ps",
            "lost_atoms_or_error",
            "dangerous_builds",
        }
        if (
            len(initial_md_rows) != 15
            or not rows_have_fields(initial_md_rows, initial_md_fields)
            or any(
                row["completed_100ps"] != "True"
                or row["lost_atoms_or_error"] != "False"
                or row["dangerous_builds"] != "0"
                for row in initial_md_rows
            )
        ):
            errors.append("initial MD package is not strict 15/15")

    production_md_path = OUTPUT / "results/production_md_runs.csv"
    if production_md_path.exists():
        with production_md_path.open(newline="", encoding="utf-8") as handle:
            production_md_rows = list(csv.DictReader(handle))
        production_md_fields = {
            "completed_target",
            "lost_atoms_or_error",
            "dangerous_builds",
        }
        if (
            len(production_md_rows) != 18
            or not rows_have_fields(production_md_rows, production_md_fields)
            or any(
                row["completed_target"] != "True"
                or row["lost_atoms_or_error"] != "False"
                or row["dangerous_builds"] != "0"
                for row in production_md_rows
            )
        ):
            errors.append("production MD package is not strict 18/18")

    sampled_msd_path = OUTPUT / "results/review_md_msd_traces_sampled.csv"
    if sampled_msd_path.exists():
        with sampled_msd_path.open(newline="", encoding="utf-8") as handle:
            sampled_msd_rows = list(csv.DictReader(handle))
        sampled_msd_fields = {
            "structure",
            "model_family",
            "seed",
            "time_ps",
            "msd_xy_a2",
        }
        if (
            len(sampled_msd_rows) != 1818
            or not rows_have_fields(sampled_msd_rows, sampled_msd_fields)
            or {row["model_family"] for row in sampled_msd_rows}
            != {"finetuned_reference", "committee_model"}
            or any(
                not math.isfinite(float(row["time_ps"]))
                or not math.isfinite(float(row["msd_xy_a2"]))
                for row in sampled_msd_rows
            )
        ):
            errors.append("sampled MSD trace table is not the validated 1818-row set")

    extended_snapshots = OUTPUT / "results/extended_snapshot_dft_evidence.csv"
    if extended_snapshots.exists():
        with extended_snapshots.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        extended_fields = {
            "completed",
            "electronic_converged_marker",
            "final_scf_iteration",
            "nelm",
            "fatal_error",
            "usable_dft_energy_ev",
            "outcar_sha256",
        }
        if (
            len(rows) != 7
            or not rows_have_fields(rows, extended_fields)
            or any(
                row["completed"] != "True"
                or row["electronic_converged_marker"] != "True"
                or int(row["final_scf_iteration"]) >= int(row["nelm"])
                or row["fatal_error"] != "False"
                or not row["usable_dft_energy_ev"]
                or len(row["outcar_sha256"]) != 64
                for row in rows
            )
        ):
            errors.append("extended snapshot package is not strict 7/7")

    training_audit = OUTPUT / "results/training_label_scf_audit.csv"
    if training_audit.exists():
        with training_audit.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        training_fields = {
            "source_kind",
            "strictly_converged",
            "final_scf_iteration",
            "nelm",
            "outcar_sha256",
        }
        source_counts = (
            {
                kind: sum(row["source_kind"] == kind for row in rows)
                for kind in {row["source_kind"] for row in rows}
            }
            if rows_have_fields(rows, training_fields)
            else {}
        )
        if (
            len(rows) != 273
            or not rows_have_fields(rows, training_fields)
            or source_counts
            != {
                "ionic_relaxation": 194,
                "fixed_geometry_single_point": 79,
            }
            or any(
                row["strictly_converged"] != "True"
                or int(row["final_scf_iteration"]) >= int(row["nelm"])
                or len(row["outcar_sha256"]) != 64
                for row in rows
            )
        ):
            errors.append("training-label SCF audit is not strict 273/273")

    relaxed_summary = OUTPUT / "results/relaxed_structure_dft_summary.csv"
    if relaxed_summary.exists():
        with relaxed_summary.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        relaxed_fields = {
            "family",
            "ionic_steps",
            "ionic_converged",
            "final_max_force_ev_a",
            "final_total_moment_mu_b",
            "outcar_sha256",
        }
        if (
            len(rows) != 5
            or not rows_have_fields(rows, relaxed_fields)
            or {row["family"] for row in rows}
            != {family for family, _ in RELAXED_FAMILIES}
            or any(
                row["ionic_converged"] != "True"
                or int(row["ionic_steps"]) <= 0
                or not math.isfinite(float(row["final_max_force_ev_a"]))
                or float(row["final_max_force_ev_a"]) >= 0.02
                or not math.isfinite(float(row["final_total_moment_mu_b"]))
                or len(row["outcar_sha256"]) != 64
                for row in rows
            )
        ):
            errors.append("relaxed-structure DFT summary is not strict 5/5")

        expected_natoms = {
            row["family"]: int(row["natoms"])
            for row in rows
            if rows_have_fields(rows, relaxed_fields | {"natoms"})
        }
        for family, _ in RELAXED_FAMILIES:
            structure = OUTPUT / f"structures/relaxed/{family}.vasp"
            if not structure.is_file():
                continue
            try:
                lines = structure.read_text(encoding="utf-8").splitlines()
                atom_count = sum(int(value) for value in lines[6].split())
                coordinate_mode = lines[7].strip().lower()
                coordinates = lines[8 : 8 + atom_count]
                if (
                    atom_count != expected_natoms.get(family)
                    or coordinate_mode not in {"direct", "cartesian"}
                    or len(coordinates) != atom_count
                    or any(len(line.split()) < 3 for line in coordinates)
                ):
                    raise ValueError("atom count or coordinate block mismatch")
            except (IndexError, ValueError) as exc:
                errors.append(f"invalid relaxed structure {family}: {exc}")

    balanced_status = OUTPUT / "results/balanced_perturbation_dft_status.csv"
    if balanced_status.exists():
        with balanced_status.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        balanced_fields = {
            "family",
            "completed",
            "electronic_converged",
            "final_scf_iteration",
            "nelm",
            "fatal",
            "forces_readable",
            "usable",
            "outcar_sha256",
        }
        balanced_fields_ok = rows_have_fields(rows, balanced_fields)
        if (
            len(rows) != 25
            or not balanced_fields_ok
            or any(
                row["completed"] != "True"
                or row["electronic_converged"] != "True"
                or int(row["final_scf_iteration"]) >= int(row["nelm"])
                or row["fatal"] != "False"
                or row["forces_readable"] != "True"
                or row["usable"] != "True"
                or len(row["outcar_sha256"]) != 64
                for row in rows
            )
        ):
            errors.append("balanced DFT package is not complete and converged 25/25")
        if balanced_fields_ok:
            family_counts = {
                family: sum(row["family"] == family for row in rows)
                for family in {row["family"] for row in rows}
            }
            if sorted(family_counts.values()) != [5, 5, 5, 5, 5]:
                errors.append(
                    f"balanced DFT family counts are not 5x5: {family_counts}"
                )

    d3_sites = OUTPUT / "results/d3_site_adsorption_energies.csv"
    if d3_sites.exists():
        with d3_sites.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        d3_fields = {
            "family",
            "completed",
            "electronic_converged",
            "final_scf_iteration",
            "nelm",
            "fatal",
            "forces_readable",
            "substrate_forces_readable",
            "li_atom_forces_readable",
            "reference_jobs_usable",
            "usable",
            "outcar_sha256",
            "substrate_outcar_sha256",
            "li_atom_outcar_sha256",
        }
        d3_fields_ok = rows_have_fields(rows, d3_fields)
        if (
            len(rows) != 15
            or not d3_fields_ok
            or any(
                row["completed"] != "True"
                or row["electronic_converged"] != "True"
                or int(row["final_scf_iteration"]) >= int(row["nelm"])
                or row["fatal"] != "False"
                or row["forces_readable"] != "True"
                or row["substrate_forces_readable"] != "True"
                or row["li_atom_forces_readable"] != "True"
                or row["reference_jobs_usable"] != "True"
                or row["usable"] != "True"
                or len(row["outcar_sha256"]) != 64
                or len(row["substrate_outcar_sha256"]) != 64
                or len(row["li_atom_outcar_sha256"]) != 64
                for row in rows
            )
        ):
            errors.append("D3 site package is not complete and converged 15/15")
        if d3_fields_ok:
            family_counts = {
                family: sum(row["family"] == family for row in rows)
                for family in {row["family"] for row in rows}
            }
            if sorted(family_counts.values()) != [3, 3, 3, 3, 3]:
                errors.append(
                    f"D3 site family counts are not 5x3: {family_counts}"
                )

    initial_snapshots = OUTPUT / "results/initial_snapshot_dft_evidence.csv"
    if initial_snapshots.exists():
        with initial_snapshots.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        snapshot_fields = {
            "completed",
            "electronic_converged_marker",
            "final_scf_iteration",
            "nelm",
            "fatal_error",
            "forces_readable",
            "scf_provenance",
            "outcar_sha256",
        }
        if (
            len(rows) != 9
            or not rows_have_fields(rows, snapshot_fields)
            or any(
                row["completed"] != "True"
                or row["electronic_converged_marker"] != "True"
                or int(row["final_scf_iteration"]) >= int(row["nelm"])
                or row["fatal_error"] != "False"
                or row["forces_readable"] != "True"
                or row["scf_provenance"]
                not in {
                    "strict_original",
                    "two_stage_algo_all_rerun",
                }
                or len(row["outcar_sha256"]) != 64
                for row in rows
            )
        ):
            errors.append("high-displacement snapshot package is not strict 9/9")

    balanced_errors = OUTPUT / "results/balanced_perturbation_force_errors.csv"
    if balanced_errors.exists():
        with balanced_errors.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        force_fields_ok = rows_have_fields(rows, {"model"})
        model_counts = (
            {
                model: sum(row["model"] == model for row in rows)
                for model in {row["model"] for row in rows}
            }
            if force_fields_ok
            else {}
        )
        if (
            len(rows) != 50
            or not force_fields_ok
            or model_counts
            != {
                "foundation_mpa0": 25,
                "grouped_e0": 25,
            }
        ):
            errors.append(f"balanced force-error table is not 2x25: {model_counts}")

    balanced_summary = OUTPUT / "results/balanced_perturbation_force_summary.csv"
    if balanced_summary.exists():
        with balanced_summary.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 12:
            errors.append(f"balanced force summary row count is not 12: {len(rows)}")

    readme = OUTPUT / "README.md"
    if readme.exists() and (
        "will be made public immediately after manuscript submission"
        in readme.read_text(encoding="utf-8")
    ):
        errors.append(
            "public README contains a submission-stage GitHub publication promise"
        )
    return errors


def main() -> int:
    global EVIDENCE_ROOT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the existing package without rebuilding it.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=EVIDENCE_ROOT,
        help="Repository root containing full local evidence files.",
    )
    args = parser.parse_args()
    EVIDENCE_ROOT = args.evidence_root.resolve()

    if not args.check:
        build()
    errors = verify()
    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    total_bytes = sum(path.stat().st_size for path in package_files())
    print(
        "PASSED FAIR submission-data package: "
        f"files={len(package_files())} bytes={total_bytes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
