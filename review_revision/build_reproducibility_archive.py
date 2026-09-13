#!/usr/bin/env python3
"""Build and verify the version-pinned journal reproducibility ZIP."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "LICENSE",
    "README.md",
    "REPRODUCIBILITY_ARCHIVE_MANIFEST.md",
    "manuscript/compile_manuscript.sh",
    "manuscript/graphical_abstract.png",
    "manuscript/graphical_abstract_caption.txt",
    "manuscript/li_mace_graphene_draft.tex",
    "manuscript/references.bib",
    "manuscript/results_scientific_reframe.tex",
    *{f"manuscript/evidence_{name}.tex" for name in (
        "dataset_counts", "mace_errors", "concurrent_learning", "d3_sites",
        "balanced_force", "site_scan", "path_scan", "path_scans", "md_traces",
        "md_runs", "initial_snapshots", "extended_snapshots",
    )},
    "manuscript/figures/dataset_family_counts.png",
    "manuscript/figures/path_profiles_revised.pdf",
    "manuscript/figures/path_profiles_revised.png",
    "manuscript/figures/review_md_extended_msd_xy_traces.pdf",
    "manuscript/figures/review_md_extended_msd_xy_traces.png",
    "manuscript/figures/scientific_summary_strengthened.pdf",
    "manuscript/figures/scientific_summary_strengthened.png",
    "manuscript/figures/site_energy_rankings_revised.pdf",
    "manuscript/figures/site_energy_rankings_revised.png",
    "manuscript/figures/structure_models.png",
    "make_review_revised_figures.py",
    "make_structure_figure.py",
    "review_revision/build_fair_submission_data.py",
    "review_revision/build_reproducibility_archive.py",
    "review_revision/archive_md_snapshot_evidence.py",
    "review_revision/audit_training_label_scf.py",
    "review_revision/collect_balanced_perturbation_dft.py",
    "review_revision/collect_d3_site_robustness.py",
    "review_revision/collect_md_snapshot_dft_checks.py",
    "review_revision/evaluate_balanced_perturbation_forces.py",
    "review_revision/evaluate_mace_snapshot_forces.py",
    "review_revision/plot_graphical_abstract_reframe.py",
    "review_revision/plot_dataset_family_counts.py",
    "review_revision/plot_science_strengthening_summary.py",
    "review_revision/plot_si_msd_traces.py",
    "review_revision/plot_si_site_path.py",
    "review_revision/prepare_balanced_perturbation_dft.py",
    "review_revision/prepare_d3_site_converged_jobs.py",
    "review_revision/prepare_d3_site_robustness_jobs.py",
    "review_revision/prepare_high_displacement_converged_jobs.py",
    "review_revision/run_cpu_science_strengthening_postprocess.sh",
    "review_revision/static_check_manuscript.py",
    "review_revision/submit_cpu_balanced_perturbation_dft_array.slurm",
    "review_revision/submit_cpu_d3_site_converged_array.slurm",
    "review_revision/submit_cpu_high_displacement_converged_array.slurm",
    "review_revision/verify_resubmission_science.py",
    "structures/vasp/POSCAR_A_Perfect.vasp",
    "structures/vasp/POSCAR_B1_Monovacancy.vasp",
    "structures/vasp/POSCAR_B2_Divacancy.vasp",
    "structures/vasp/POSCAR_C_StoneWales.vasp",
    "structures/vasp/POSCAR_D_SiGraphene.vasp",
    "structures/vasp/structure_summary.json",
    "submission_data/MANIFEST.sha256",
    "submission_data/DATA_LICENSE.md",
    "submission_data/README.md",
    "submission_data/design/BALANCED_PERTURBATION_DESIGN.md",
    "submission_data/design/D3_SITE_DESIGN.md",
    "submission_data/design/balanced_perturbation_manifest.csv",
    "submission_data/design/d3_site_manifest.csv",
    "submission_data/design/HIGH_DISPLACEMENT_SCF_DESIGN.md",
    "submission_data/design/high_displacement_manifest.csv",
    "submission_data/models/README.md",
    "submission_data/models/li_mace_grouped_e0_seed20260430.model",
    "submission_data/models/li_mace_review_seed20260427.model",
    "submission_data/models/li_mace_review_seed20260428.model",
    "submission_data/models/li_mace_review_seed20260429.model",
    "submission_data/models/li_mace_v1_3060ti.model",
    "submission_data/results/extended_snapshot_dft_evidence.csv",
    "submission_data/results/foundation_snapshot_force_errors.csv",
    "submission_data/results/foundation_snapshot_force_summary.csv",
    "submission_data/results/grouped_e0_snapshot_force_errors.csv",
    "submission_data/results/grouped_e0_snapshot_force_summary.csv",
    "submission_data/results/high_displacement_dft.extxyz",
    "submission_data/results/initial_snapshot_dft_evidence.csv",
    "submission_data/results/balanced_perturbation_dft.extxyz",
    "submission_data/results/balanced_perturbation_dft_status.csv",
    "submission_data/results/balanced_perturbation_force_errors.csv",
    "submission_data/results/balanced_perturbation_force_summary.csv",
    "submission_data/results/d3_site_adsorption_energies.csv",
    "submission_data/results/d3_site_family_summary.csv",
    "submission_data/results/d3_site_structures.extxyz",
    "submission_data/results/initial_md_aggregate.csv",
    "submission_data/results/initial_md_runs.csv",
    "submission_data/results/review_md_msd_traces_sampled.csv",
    "submission_data/results/relaxed_structure_dft_summary.csv",
    "submission_data/results/training_label_scf_audit.csv",
    "submission_data/structures/relaxed/A_Perfect.vasp",
    "submission_data/structures/relaxed/B1_Monovacancy.vasp",
    "submission_data/structures/relaxed/B2_Divacancy.vasp",
    "submission_data/structures/relaxed/C_StoneWales.vasp",
    "submission_data/structures/relaxed/D_SiGraphene.vasp",
}

FORBIDDEN_BASENAMES = {
    "POTCAR",
    "OUTCAR",
    "WAVECAR",
    "CHGCAR",
    "CHG",
    "XDATCAR",
    "vasprun.xml",
}

FORBIDDEN_PATH_PARTS = {
    "__pycache__",
    "gpu_local_transfer_bundle",
    "local_5080_reviewer_gpu_pack",
    "skills",
}

FORBIDDEN_FILES = {
    "AGENT_PROJECT_STATUS.md",
    "AGENT_REPRODUCE_REPORT.md",
    "LOCAL_5080_DOWNLOAD_AND_AGENT_PROMPT.md",
    "README_DATA_EXPANSION.md",
    "README_TWO_DAY_RUSH.md",
    "manuscript/cover_letter_computational_materials_science.txt",
    "manuscript/highlights.txt",
    "manuscript/figures/md_800k_temperature_energy.png",
    "manuscript/figures/path_profiles.png",
    "manuscript/figures/site_energy_rankings.png",
    "manuscript/figures/training_curve.png",
    "submission_data/results/adsorption_energies.csv",
}

FORBIDDEN_DOC_SNIPPETS = {
    "Use Slurm for CPU and GPU jobs on the cluster",
    "sbatch submit_gpu_",
    "approximate barriers",
    "will be made public immediately after manuscript submission",
    "github.com/xiaohuang-6/Li-vasp",
    "intended for public deposition",
    "A public release must declare",
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def resolve_commit(revision: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        cwd=ROOT,
        text=True,
    ).strip()


def archive_members(archive: zipfile.ZipFile) -> tuple[str, dict[str, zipfile.ZipInfo]]:
    files = [item for item in archive.infolist() if not item.is_dir()]
    roots = {PurePosixPath(item.filename).parts[0] for item in files}
    if len(roots) != 1:
        raise ValueError(f"archive must contain one top-level directory, found {sorted(roots)}")
    prefix = next(iter(roots))
    relative = {
        PurePosixPath(item.filename).relative_to(prefix).as_posix(): item
        for item in files
    }
    return prefix, relative


def verify_archive(path: Path, expected_commit: str | None = None) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing archive: {path}"]

    try:
        with zipfile.ZipFile(path) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                errors.append(f"corrupt ZIP entry: {corrupt}")
            try:
                prefix, members = archive_members(archive)
            except ValueError as exc:
                return [str(exc)]

            missing = sorted(REQUIRED_FILES - set(members))
            if missing:
                errors.append(f"required files missing: {missing}")

            forbidden = sorted(FORBIDDEN_FILES & set(members))
            if forbidden:
                errors.append(f"non-journal files exported: {forbidden}")

            for info in archive.infolist():
                pure = PurePosixPath(info.filename)
                if pure.parts == (prefix,):
                    continue
                relative = pure.relative_to(prefix)
                if any(part in FORBIDDEN_PATH_PARTS for part in relative.parts):
                    errors.append(f"forbidden project-history path: {relative.as_posix()}")

            for relative, info in members.items():
                pure = PurePosixPath(relative)
                if pure.name in FORBIDDEN_BASENAMES:
                    errors.append(f"forbidden licensed/heavy file: {relative}")
                if pure.name.startswith(".nfs") or pure.suffix in {".pyc", ".zip"}:
                    errors.append(f"forbidden generated file: {relative}")
                if pure.suffix.lower() in {".md", ".txt", ".tex"}:
                    text = archive.read(info).decode("utf-8", errors="replace")
                    for snippet in FORBIDDEN_DOC_SNIPPETS:
                        if snippet in text:
                            errors.append(
                                f"stale or unsafe documentation in {relative}: {snippet!r}"
                            )

            if expected_commit is not None:
                comment = archive.comment.decode("ascii", errors="replace").strip()
                if comment != expected_commit:
                    errors.append(
                        f"ZIP commit comment mismatch: {comment!r} != {expected_commit!r}"
                    )
    except zipfile.BadZipFile as exc:
        errors.append(f"invalid ZIP archive: {exc}")
    return errors


def build_archive(revision: str, output: Path | None) -> tuple[Path, str]:
    commit = resolve_commit(revision)
    short = commit[:7]
    if output is None:
        output = ROOT / "manuscript" / f"Li-vasp_reproducibility_{short}.zip"
    elif not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git",
            "archive",
            "--format=zip",
            f"--prefix=Li-vasp_reproducibility_{short}/",
            f"--output={output}",
            commit,
        ],
        cwd=ROOT,
        check=True,
    )
    with zipfile.ZipFile(output, mode="a") as archive:
        archive.comment = commit.encode("ascii")
    return output, commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", default="HEAD", help="Git commit to export.")
    parser.add_argument("--output", type=Path, help="Output ZIP path.")
    parser.add_argument(
        "--check",
        type=Path,
        metavar="ARCHIVE",
        help="Verify an existing ZIP instead of building one.",
    )
    args = parser.parse_args()

    if args.check is not None:
        path = args.check if args.check.is_absolute() else ROOT / args.check
        expected_commit = None
    else:
        path, expected_commit = build_archive(args.commit, args.output)

    errors = verify_archive(path, expected_commit)
    if errors:
        print("FAILED reproducibility archive")
        for error in errors:
            print(f"- {error}")
        return 1

    with zipfile.ZipFile(path) as archive:
        file_count = sum(not item.is_dir() for item in archive.infolist())
        comment = archive.comment.decode("ascii", errors="replace").strip() or "unknown"
    print(
        "PASSED reproducibility archive: "
        f"commit={comment} files={file_count} bytes={path.stat().st_size} "
        f"sha256={digest(path)} path={path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
