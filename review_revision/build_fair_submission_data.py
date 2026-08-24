#!/usr/bin/env python3
"""Build and verify a compact, path-sanitized submission data package."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT
OUTPUT = ROOT / "submission_data"

COPY_FILES = {
    "data/mace_datasets/li_mace_train.extxyz": "datasets/original_split/train.extxyz",
    "data/mace_datasets/li_mace_valid.extxyz": "datasets/original_split/valid.extxyz",
    "data/mace_datasets/li_mace_test.extxyz": "datasets/original_split/test.extxyz",
    "data/mace_datasets/li_mace_dataset_report.json": "datasets/original_split/report.json",
    "data/mace_datasets_grouped/li_mace_grouped_train.extxyz": "datasets/grouped_split/train.extxyz",
    "data/mace_datasets_grouped/li_mace_grouped_valid.extxyz": "datasets/grouped_split/valid.extxyz",
    "data/mace_datasets_grouped/li_mace_grouped_test.extxyz": "datasets/grouped_split/test.extxyz",
    "data/mace_datasets_grouped/li_mace_grouped_dataset_report.json": "datasets/grouped_split/report.json",
    "results/review_revision/adsorption_energy_analysis/adsorption_energies.csv": "results/adsorption_energies.csv",
    "results/review_revision/gpu_analysis_20260725_0116/mace_eval_summary.csv": "results/mace_eval_summary.csv",
    "results/review_revision/gpu_analysis_20260725_0116/committee_summary.csv": "results/committee_summary.csv",
    "results/review_revision/gpu_analysis/review_md_runs.csv": "results/initial_md_runs.csv",
    "results/review_revision/gpu_analysis/review_md_aggregate.csv": "results/initial_md_aggregate.csv",
    "results/review_revision/gpu_analysis_20260725_0116/review_md_runs.csv": "results/production_md_runs.csv",
    "results/review_revision/gpu_analysis_20260725_0116/review_md_aggregate.csv": "results/production_md_aggregate.csv",
    "review_revision/SNAPSHOT_DFT_EVIDENCE.csv": "results/initial_snapshot_dft_evidence.csv",
    "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/foundation_mpa0_snapshot_force_errors.csv": "results/foundation_snapshot_force_errors.csv",
    "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/foundation_mpa0_snapshot_force_summary.csv": "results/foundation_snapshot_force_summary.csv",
    "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/grouped_e0_snapshot_force_errors.csv": "results/grouped_e0_snapshot_force_errors.csv",
    "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/grouped_e0_snapshot_force_summary.csv": "results/grouped_e0_snapshot_force_summary.csv",
    "results/two_day_rush/path_barriers.csv": "results/fixed_path_descriptors.csv",
    "results/two_day_rush/path_profiles.csv": "results/fixed_path_profiles.csv",
    "results/two_day_rush/site_energy_rankings.csv": "results/fixed_site_energies.csv",
    "results/two_day_rush/training_curve.csv": "results/training_curve.csv",
}

TEXT_FILES = {
    "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/logs/agent_grouped_e0_finetune.log": "logs/grouped_e0_training_audit.log",
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


def package_files() -> list[Path]:
    return sorted(
        path
        for path in OUTPUT.rglob("*")
        if path.is_file() and path.name != "MANIFEST.sha256"
    )


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
        "results/initial_md_aggregate.csv",
        "results/initial_md_runs.csv",
        "results/production_md_aggregate.csv",
        "results/production_md_runs.csv",
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

    expected_extxyz = {
        "datasets/original_split/train.extxyz": 211,
        "datasets/original_split/valid.extxyz": 31,
        "datasets/original_split/test.extxyz": 31,
        "datasets/grouped_split/train.extxyz": 263,
        "datasets/grouped_split/valid.extxyz": 5,
        "datasets/grouped_split/test.extxyz": 5,
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
        if len(initial_md_rows) != 15:
            errors.append(
                f"initial MD row count mismatch: {len(initial_md_rows)} != 15"
            )
        if any(row["completed_100ps"] != "True" for row in initial_md_rows):
            errors.append("initial MD package contains an incomplete trajectory")
        if any(
            row["lost_atoms_or_error"] != "False" for row in initial_md_rows
        ):
            errors.append("initial MD package contains a lost-atom/error run")
        if any(row["dangerous_builds"] != "0" for row in initial_md_rows):
            errors.append("initial MD package contains dangerous neighbor builds")

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
