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
    "manuscript/make_graphical_abstract.py",
    "manuscript/references.bib",
    "manuscript/figures/dataset_family_counts.png",
    "manuscript/figures/path_profiles_revised.png",
    "manuscript/figures/review_mace_foundation_comparison.png",
    "manuscript/figures/review_md_extended_msd_xy_traces.png",
    "manuscript/figures/site_energy_rankings_revised.png",
    "manuscript/figures/structure_models.png",
    "review_revision/build_fair_submission_data.py",
    "review_revision/build_reproducibility_archive.py",
    "review_revision/static_check_manuscript.py",
    "review_revision/verify_manuscript_numbers.py",
    "submission_data/MANIFEST.sha256",
    "submission_data/README.md",
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
}

FORBIDDEN_DOC_SNIPPETS = {
    "Use Slurm for CPU and GPU jobs on the cluster",
    "sbatch submit_gpu_",
    "approximate barriers",
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
