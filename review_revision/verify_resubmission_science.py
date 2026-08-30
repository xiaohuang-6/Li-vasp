#!/usr/bin/env python3
"""Verify the reframed manuscript's central numerical claims against evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_MODEL_HASHES = {
    "li_mace_v1_3060ti.model":
        "2b5227ce65cc392bcba62cbdafd345a1be1fd31ebb0ca295e364f53d54b919d1",
    "li_mace_review_seed20260427.model":
        "0811bed40f55755393b86c53edc0ec500cb8ad76d46b8393aad214f4a800d0b3",
    "li_mace_review_seed20260428.model":
        "43102d78a25b8e8904db1cfda24a8e4105276980d65a4d1bcc9587de77f8d3e4",
    "li_mace_review_seed20260429.model":
        "ae4fdce775236e5f9689387257402136877c7543e3cd1b71efd13750e6e9f7c1",
    "li_mace_grouped_e0_seed20260430.model":
        "2abd951d5c8dcf13925eb6e5d0974e4790373d288b35d711d24787cd0e629dcf",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def first_existing(root: Path, *relative_paths: str) -> Path:
    for relative in relative_paths:
        path = root / relative
        if path.is_file():
            return path
    raise FileNotFoundError(
        "none of the evidence paths exists: "
        + ", ".join(str(root / relative) for relative in relative_paths)
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def relaxed_outcar_state(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    moments = re.findall(
        r"number of electron\s+[+-]?[0-9.]+\s+magnetization\s+([+-]?[0-9.]+)",
        text,
    )
    nions_match = re.search(r"\bNIONS\s*=\s*(\d+)", text)
    if not moments or nions_match is None:
        raise ValueError(f"relaxed-state metadata not found in {path}")
    nions = int(nions_match.group(1))
    lines = text.splitlines()
    force_starts = [
        index
        for index, line in enumerate(lines)
        if "POSITION" in line and "TOTAL-FORCE" in line
    ]
    if not force_starts:
        raise ValueError(f"no TOTAL-FORCE block in {path}")
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
            f"expected {nions} final force rows in {path}, found {len(force_norms)}"
        )
    moment = float(moments[-1])
    return {
        "ionic_steps": len(force_starts),
        "ionic_converged": (
            "reached required accuracy - stopping structural energy minimisation"
            in text
        ),
        "final_max_force_ev_a": max(force_norms),
        "final_total_moment_mu_b": 0.0 if abs(moment) < 0.0005 else moment,
        "outcar_sha256": digest(path),
    }


def read_tex_tree(path: Path, seen: set[Path] | None = None) -> str:
    visited = set() if seen is None else seen
    path = path.resolve()
    if path in visited:
        return ""
    visited.add(path)
    text = path.read_text(encoding="utf-8")
    pieces: list[str] = []
    cursor = 0
    for match in re.finditer(r"\\input\{([^}]+)\}", text):
        pieces.append(text[cursor : match.start()])
        child = path.parent / match.group(1)
        if child.suffix == "":
            child = child.with_suffix(".tex")
        pieces.append(read_tex_tree(child, visited))
        cursor = match.end()
    pieces.append(text[cursor:])
    return "".join(pieces)


def require(text: str, snippet: str, label: str) -> None:
    normalized_text = " ".join(text.split())
    normalized_snippet = " ".join(snippet.split())
    if normalized_snippet not in normalized_text:
        raise AssertionError(f"missing {label}: {snippet!r}")


def row_by(
    rows: list[dict[str, str]], **criteria: str
) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(row.get(key) == value for key, value in criteria.items())
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one row for {criteria}, found {len(matches)}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT,
        help="Repository root containing full local evidence files.",
    )
    parser.add_argument(
        "--tex",
        type=Path,
        default=ROOT / "manuscript/li_mace_graphene_draft.tex",
    )
    parser.add_argument(
        "--si",
        type=Path,
        default=ROOT / "manuscript/supporting_information.tex",
    )
    parser.add_argument(
        "--response",
        type=Path,
        default=ROOT / "manuscript/response_to_reviewers.tex",
    )
    parser.add_argument(
        "--archive-only",
        action="store_true",
        help="Skip the separately uploaded response-letter source check.",
    )
    args = parser.parse_args()
    evidence = args.evidence_root.resolve()
    text = read_tex_tree(args.tex)
    si = args.si.read_text(encoding="utf-8")
    if args.archive_only:
        response = ""
    else:
        response = args.response.read_text(encoding="utf-8")
    combined = text + "\n" + si
    checks = 0

    try:
        require(
            text,
            "Machine-learning interatomic potentials for battery materials",
            "scientific title",
        )
        require(text, "These authors contributed equally", "first-page equal contribution")
        require(
            text,
            "Yuhan Sun and Xiao Huang contributed equally to Conceptualization",
            "author-contribution equality",
        )
        if "Declaration of generative AI" in text:
            raise AssertionError("non-required generative-AI declaration remains")
        abstract = re.search(
            r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, flags=re.DOTALL
        )
        if abstract is None:
            raise AssertionError("abstract not found")
        if "285.2" in abstract.group(1) or "20.1" in abstract.group(1):
            raise AssertionError("correlated same-workflow metric remains in Abstract")
        if "will be made public immediately after manuscript submission" in combined:
            raise AssertionError("submission-stage publication promise remains")
        if "corresponding public source snapshot" in combined:
            raise AssertionError("private development repository is described as public")
        require(
            text,
            "A version-pinned reproducibility archive is provided with this article as Supplementary Data.",
            "article-linked supplementary archive statement",
        )
        checks += 8

        if not args.archive_only:
            require(response, r"\section*{General response}", "general reviewer response")
            require(response, r"\section*{Reviewer 2}", "Reviewer 2 response section")
            require(response, r"\section*{Reviewer 3}", "Reviewer 3 response section")
            reviewer_2 = response.split(r"\section*{Reviewer 2}", maxsplit=1)[1].split(
                r"\section*{Reviewer 3}", maxsplit=1
            )[0]
            for comment in range(1, 9):
                require(
                    reviewer_2,
                    rf"\subsection*{{Comment {comment}:",
                    f"Reviewer 2 comment {comment} response",
                )
            reviewer_3 = response.split(r"\section*{Reviewer 3}", maxsplit=1)[1]
            for comment in range(1, 5):
                require(
                    reviewer_3,
                    rf"\subsection*{{Comment {comment}:",
                    f"Reviewer 3 comment {comment} response",
                )
            require(response, r"\section*{Closing statement}", "response closing statement")
            checks += 16

        report = json.loads(
            first_existing(
                evidence,
                "data/mace_datasets/li_mace_dataset_report.json",
                "submission_data/datasets/original_split/report.json",
            ).read_text(encoding="utf-8")
        )
        grouped = json.loads(
            first_existing(
                evidence,
                "data/mace_datasets_grouped/li_mace_grouped_dataset_report.json",
                "submission_data/datasets/grouped_split/report.json",
            ).read_text(encoding="utf-8")
        )
        if report["n_frames"] != 273 or grouped["frame_counts"] != {
            "train": 263,
            "valid": 5,
            "test": 5,
        }:
            raise AssertionError("dataset or grouped-split counts changed")
        require(combined, "contains 273", "dataset size")
        require(
            combined,
            "263 training frames, 5 validation frames, and 5 test frames",
            "grouped split",
        )
        training_audit = read_csv(
            first_existing(
                evidence,
                "results/review_revision/training_label_scf_audit.csv",
                "submission_data/results/training_label_scf_audit.csv",
            )
        )
        source_counts = {
            kind: sum(row["source_kind"] == kind for row in training_audit)
            for kind in {row["source_kind"] for row in training_audit}
        }
        if len(training_audit) != 273 or source_counts != {
            "ionic_relaxation": 194,
            "fixed_geometry_single_point": 79,
        } or any(
            row["strictly_converged"] != "True"
            or int(row["final_scf_iteration"]) >= int(row["nelm"])
            or len(row["outcar_sha256"]) != 64
            for row in training_audit
        ):
            raise AssertionError("training-label SCF audit is not strict 273/273")
        require(text, "273-row audit table", "training-label SCF audit statement")
        moment_families = [
            "A_Perfect",
            "B1_Monovacancy",
            "B2_Divacancy",
            "C_StoneWales",
            "D_SiGraphene",
        ]
        raw_relaxed = [
            evidence / "dft_outputs" / family / "OUTCAR"
            for family in moment_families
        ]
        if all(path.is_file() for path in raw_relaxed):
            relaxed_rows = {
                family: relaxed_outcar_state(path)
                for family, path in zip(moment_families, raw_relaxed, strict=True)
            }
        else:
            curated_relaxed = read_csv(
                first_existing(
                    evidence,
                    "results/review_revision/relaxed_structure_dft_summary.csv",
                    "submission_data/results/relaxed_structure_dft_summary.csv",
                )
            )
            if len(curated_relaxed) != 5:
                raise AssertionError("relaxed-structure summary must contain five rows")
            relaxed_rows = {row["family"]: row for row in curated_relaxed}
        if set(relaxed_rows) != set(moment_families):
            raise AssertionError("relaxed-structure family coverage changed")
        for family, row in relaxed_rows.items():
            if (
                str(row["ionic_converged"]) != "True"
                or int(row["ionic_steps"]) <= 0
                or not math.isfinite(float(row["final_max_force_ev_a"]))
                or float(row["final_max_force_ev_a"]) >= 0.02
                or not math.isfinite(float(row["final_total_moment_mu_b"]))
                or len(str(row["outcar_sha256"])) != 64
            ):
                raise AssertionError(f"relaxed-structure evidence failed for {family}")
        final_moments = [
            float(relaxed_rows[family]["final_total_moment_mu_b"])
            for family in moment_families
        ]
        final_max_forces = [
            float(relaxed_rows[family]["final_max_force_ev_a"])
            for family in moment_families
        ]
        formatted_moments = ", ".join(f"{value:.3f}" for value in final_moments[:-1])
        formatted_moments += f", and {final_moments[-1]:.3f}"
        require(
            text,
            "Initial magnetic moments were 0.1 $\\mu_{\\mathrm B}$ on C and Si "
            "and 1.0 $\\mu_{\\mathrm B}$ on Li",
            "spin initialization",
        )
        require(text, formatted_moments, "final relaxed-structure magnetic moments")
        require(
            text,
            f"{min(final_max_forces):.4f}--{max(final_max_forces):.4f} eV",
            "relaxed-structure final maximum-force range",
        )
        checks += 9

        expected_families = {
            "A_Perfect",
            "B1_Monovacancy",
            "B2_Divacancy",
            "C_StoneWales",
            "D_SiGraphene",
        }
        d3_rows = read_csv(
            first_existing(
                evidence,
                "results/review_revision/d3_site_robustness_analysis/d3_site_adsorption_energies.csv",
                "submission_data/results/d3_site_adsorption_energies.csv",
            )
        )
        d3_counts = {
            family: sum(row["family"] == family for row in d3_rows)
            for family in expected_families
        }
        if len(d3_rows) != 15 or set(row["family"] for row in d3_rows) != expected_families:
            raise AssertionError("D3 site evidence must contain exactly 15 rows in five families")
        if set(d3_counts.values()) != {3}:
            raise AssertionError(f"D3 site evidence is not three-per-family: {d3_counts}")
        for row in d3_rows:
            if (
                row["completed"] != "True"
                or row["electronic_converged"] != "True"
                or int(row["final_scf_iteration"]) >= int(row["nelm"])
                or row["fatal"] != "False"
                or row["forces_readable"] != "True"
                or row["substrate_forces_readable"] != "True"
                or row["li_atom_forces_readable"] != "True"
                or row["reference_jobs_usable"] != "True"
                or row["usable"] != "True"
                or not math.isfinite(float(row["adsorption_energy_ev_per_li"]))
                or len(row["outcar_sha256"]) != 64
                or len(row["substrate_outcar_sha256"]) != 64
                or len(row["li_atom_outcar_sha256"]) != 64
            ):
                raise AssertionError(f"unusable or untraceable D3 row: {row['case']}")
        require(
            text,
            "three prespecified PBE-ranked sites per family",
            "multi-site adsorption scope",
        )
        require(
            text,
            "The absolute adsorption energies are not lithiation voltages or "
            "formation energies relative to metallic Li",
            "isolated-Li reference-state limitation",
        )
        require(si, r"\label{tab:si_d3_sites}", "D3 multi-site SI table")
        for row in d3_rows:
            require(
                si,
                f"{float(row['adsorption_energy_ev_per_li']):.3f}",
                f"D3 SI value for {row['case']}",
            )
        for family in sorted(expected_families):
            family_rows = sorted(
                (row for row in d3_rows if row["family"] == family),
                key=lambda row: int(row["pbe_fixed_site_rank"]),
            )
            family_energies = [
                float(row["adsorption_energy_ev_per_li"])
                for row in family_rows
            ]
            if any(
                family_energies[index] >= family_energies[index + 1]
                for index in range(2)
            ):
                raise AssertionError(f"D3 site rank changed for {family}")
            best = min(family_energies)
            require(text, f"{best:.3f}", f"best sampled D3 energy for {family}")
        pristine_energies = [
            float(row["adsorption_energy_ev_per_li"])
            for row in d3_rows
            if row["family"] == "A_Perfect"
        ]
        defect_energies = [
            float(row["adsorption_energy_ev_per_li"])
            for row in d3_rows
            if row["family"] != "A_Perfect"
        ]
        defect_pristine_gap = min(pristine_energies) - max(defect_energies)
        if defect_pristine_gap <= 0:
            raise AssertionError("D3 defect/pristine separation changed")
        require(text, "All 12 non-pristine", "D3 multi-site robustness")
        require(text, f"{defect_pristine_gap:.3f} eV", "D3 defect/pristine gap")
        require(
            text,
            "rank order of the three sites in every family",
            "D3 rank robustness",
        )
        checks += 25

        balanced_status = read_csv(
            first_existing(
                evidence,
                "results/review_revision/balanced_perturbation_dft_analysis/balanced_perturbation_dft_status.csv",
                "submission_data/results/balanced_perturbation_dft_status.csv",
            )
        )
        balanced_counts = {
            family: sum(row["family"] == family for row in balanced_status)
            for family in expected_families
        }
        if len(balanced_status) != 25 or set(balanced_counts.values()) != {5}:
            raise AssertionError(f"balanced DFT evidence is not five-by-five: {balanced_counts}")
        status_hashes: dict[str, str] = {}
        for row in balanced_status:
            if (
                row["completed"] != "True"
                or row["electronic_converged"] != "True"
                or int(row["final_scf_iteration"]) >= int(row["nelm"])
                or row["fatal"] != "False"
                or row["forces_readable"] != "True"
                or row["usable"] != "True"
                or len(row["outcar_sha256"]) != 64
            ):
                raise AssertionError(f"unusable balanced DFT row: {row['configuration_id']}")
            status_hashes[Path(row["job_dir"]).name] = row["outcar_sha256"]

        balanced_frames = read_csv(
            first_existing(
                evidence,
                "results/review_revision/balanced_perturbation_mace_eval/frame_errors.csv",
                "submission_data/results/balanced_perturbation_force_errors.csv",
            )
        )
        if len(balanced_frames) != 50:
            raise AssertionError("balanced model evaluation must contain exactly 50 rows")
        for model in ("foundation_mpa0", "grouped_e0"):
            model_rows = [row for row in balanced_frames if row["model"] == model]
            if len(model_rows) != 25:
                raise AssertionError(f"balanced model row count changed for {model}")
            for row in model_rows:
                if status_hashes.get(row["configuration_id"]) != row["source_outcar_sha256"]:
                    raise AssertionError(
                        f"balanced source hash mismatch: {model}/{row['configuration_id']}"
                    )

        balanced_summary = read_csv(
            first_existing(
                evidence,
                "results/review_revision/balanced_perturbation_mace_eval/summary.csv",
                "submission_data/results/balanced_perturbation_force_summary.csv",
            )
        )
        if len(balanced_summary) != 12:
            raise AssertionError("balanced summary must contain two models by six scopes")
        foundation_balanced = row_by(
            balanced_summary, model="foundation_mpa0", family="ALL"
        )
        tuned_balanced = row_by(balanced_summary, model="grouped_e0", family="ALL")
        foundation_force = float(foundation_balanced["force_rmse_mev_a_pooled"])
        tuned_force = float(tuned_balanced["force_rmse_mev_a_pooled"])
        if round(foundation_force, 1) != 450.0 or round(tuned_force, 1) != 267.5:
            raise AssertionError("balanced all-family force RMSE changed")
        require(text, "450.0 meV", "balanced foundation force RMSE")
        require(text, "267.5 meV", "balanced fine-tuned force RMSE")
        require(text, "a 40.6\\% reduction", "balanced force-RMSE reduction")
        for field, label in (
            ("li_force_rmse_mev_a_pooled", "Li-force RMSE"),
            ("substrate_force_rmse_mev_a_pooled", "substrate-force RMSE"),
        ):
            require(
                text,
                f"{float(foundation_balanced[field]):.1f} to "
                f"{float(tuned_balanced[field]):.1f}",
                label,
            )
        require(si, r"\label{tab:si_balanced_force}", "balanced SI table")
        tuned_family_forces: list[float] = []
        for family in sorted(expected_families):
            foundation_family = row_by(
                balanced_summary, model="foundation_mpa0", family=family
            )
            tuned_family = row_by(
                balanced_summary, model="grouped_e0", family=family
            )
            foundation_value = float(
                foundation_family["force_rmse_mev_a_pooled"]
            )
            tuned_value = float(tuned_family["force_rmse_mev_a_pooled"])
            tuned_family_forces.append(tuned_value)
            reduction = 100 * (foundation_value - tuned_value) / foundation_value
            require(
                text,
                f"{foundation_value:.1f} to {tuned_value:.1f}",
                f"balanced force change for {family}",
            )
            require(
                si,
                f"{reduction:.1f}",
                f"balanced force reduction for {family}",
            )
        require(
            text,
            f"{round(min(tuned_family_forces))}--{round(max(tuned_family_forces))}",
            "balanced residual family-force range",
        )
        maximum_tuned_frame = max(
            float(row["force_rmse_mev_a"])
            for row in balanced_frames
            if row["model"] == "grouped_e0"
        )
        require(
            text,
            f"{round(maximum_tuned_frame)} meV",
            "largest fine-tuned balanced frame error",
        )
        frame_errors = {
            model: {
                row["configuration_id"]: float(row["force_rmse_mev_a"])
                for row in balanced_frames
                if row["model"] == model
            }
            for model in ("foundation_mpa0", "grouped_e0")
        }
        if set(frame_errors["foundation_mpa0"]) != set(frame_errors["grouped_e0"]):
            raise AssertionError("balanced frame identifiers differ between models")
        improved_frames = sum(
            frame_errors["grouped_e0"][identifier]
            < frame_errors["foundation_mpa0"][identifier]
            for identifier in frame_errors["foundation_mpa0"]
        )
        require(
            combined,
            f"{improved_frames} of {len(frame_errors['foundation_mpa0'])}",
            "balanced per-frame improvement count",
        )
        amplitude_values: dict[tuple[str, float], float] = {}
        for model in ("foundation_mpa0", "grouped_e0"):
            for sigma in (0.03, 0.06, 0.10):
                rows = [
                    row
                    for row in balanced_frames
                    if row["model"] == model and float(row["sigma_a"]) == sigma
                ]
                expected_count = 5 if sigma == 0.03 else 10
                if len(rows) != expected_count:
                    raise AssertionError(
                        f"balanced amplitude count changed for {model}/{sigma}: "
                        f"{len(rows)}"
                    )
                squared_error_sum = sum(
                    float(row["force_rmse_mev_a"]) ** 2
                    * 3
                    * int(row["natoms"])
                    for row in rows
                )
                component_count = sum(3 * int(row["natoms"]) for row in rows)
                amplitude_values[(model, sigma)] = math.sqrt(
                    squared_error_sum / component_count
                )
        for model, label in (
            ("foundation_mpa0", "foundation"),
            ("grouped_e0", "fine-tuned"),
        ):
            for sigma in (0.03, 0.06, 0.10):
                value = amplitude_values[(model, sigma)]
                require(
                    combined,
                    f"{value:.1f}",
                    f"{label} balanced force RMSE at sigma={sigma:.2f}",
                )
        smallest_reduction = 100 * (
            amplitude_values[("foundation_mpa0", 0.03)]
            - amplitude_values[("grouped_e0", 0.03)]
        ) / amplitude_values[("foundation_mpa0", 0.03)]
        largest_reduction = 100 * (
            amplitude_values[("foundation_mpa0", 0.10)]
            - amplitude_values[("grouped_e0", 0.10)]
        ) / amplitude_values[("foundation_mpa0", 0.10)]
        require(combined, f"{smallest_reduction:.1f}\\%", "small-amplitude reduction")
        require(combined, f"{largest_reduction:.1f}\\%", "large-amplitude reduction")
        checks += 33

        mace_rows = read_csv(
            first_existing(
                evidence,
                "results/review_revision/gpu_analysis_20260725_0116/mace_eval_summary.csv",
                "submission_data/results/mace_eval_summary.csv",
            )
        )
        foundation = row_by(
            mace_rows, model_label="foundation_mpa0", split="test", family="ALL"
        )
        finetuned = row_by(
            mace_rows, model_label="finetuned_3060ti", split="test", family="ALL"
        )
        for row, label in ((foundation, "foundation"), (finetuned, "fine-tuned")):
            value = float(row["force_rmse_mev_a_frame_rms"])
            require(text, f"{value:.1f} meV", f"{label} same-workflow force RMSE")
        checks += 2

        raw_snapshot_summary = (
            evidence
            / "results/review_revision/high_displacement_mace_eval_strict/all_models_snapshot_force_summary.csv"
        )
        if raw_snapshot_summary.is_file():
            snapshot_rows = read_csv(raw_snapshot_summary)
        else:
            foundation_snapshot_rows = read_csv(
                evidence
                / "submission_data/results/foundation_snapshot_force_summary.csv"
            )
            tuned_snapshot_rows = read_csv(
                evidence
                / "submission_data/results/grouped_e0_snapshot_force_summary.csv"
            )
            for row in foundation_snapshot_rows:
                row.setdefault("model_label", "foundation_mpa0")
            for row in tuned_snapshot_rows:
                row.setdefault("model_label", "grouped_e0")
            snapshot_rows = foundation_snapshot_rows + tuned_snapshot_rows
        snapshot_rmse_exact = {
            (model, group): float(
                row_by(
                    snapshot_rows, model_label=model, group=group
                )["force_rmse_mev_a_frame_rms"]
            )
            for model in ("foundation_mpa0", "grouped_e0")
            for group in ("ALL", "B1_Monovacancy", "D_SiGraphene")
        }
        snapshot_rmse = {
            key: round(value) for key, value in snapshot_rmse_exact.items()
        }
        if any(value <= 0 for value in snapshot_rmse.values()):
            raise AssertionError("snapshot force RMSE is non-positive")
        foundation_all = snapshot_rmse[("foundation_mpa0", "ALL")]
        foundation_mono = snapshot_rmse[("foundation_mpa0", "B1_Monovacancy")]
        foundation_si = snapshot_rmse[("foundation_mpa0", "D_SiGraphene")]
        tuned_all = snapshot_rmse[("grouped_e0", "ALL")]
        tuned_mono = snapshot_rmse[("grouped_e0", "B1_Monovacancy")]
        tuned_si = snapshot_rmse[("grouped_e0", "D_SiGraphene")]
        foundation_si_exact = snapshot_rmse_exact[
            ("foundation_mpa0", "D_SiGraphene")
        ]
        tuned_si_exact = snapshot_rmse_exact[("grouped_e0", "D_SiGraphene")]
        si_change = round(
            100 * abs(foundation_si_exact - tuned_si_exact) / foundation_si_exact
        )
        si_direction = "reduction" if tuned_si < foundation_si else "increase"
        for snippet, label in (
            (
                f"from {foundation_all} to {tuned_all} meV",
                "all-snapshot force RMSE change",
            ),
            (
                f"{foundation_mono} meV",
                "foundation monovacancy snapshot force RMSE",
            ),
            (f"{foundation_si} meV", "foundation Si4 snapshot force RMSE"),
            (
                f"{tuned_mono} meV",
                "fine-tuned monovacancy snapshot force RMSE",
            ),
            (f"{tuned_si} meV", "fine-tuned Si4 snapshot force RMSE"),
        ):
            require(text, snippet, label)
        require(
            text,
            f"a {si_change}\\% {si_direction}",
            "Si4 percentage change",
        )
        checks += 7

        error_rows = read_csv(
            first_existing(
                evidence,
                "results/review_revision/high_displacement_mace_eval_strict/all_models_snapshot_force_errors.csv",
                "submission_data/results/foundation_snapshot_force_errors.csv",
            )
        )
        foundation_errors = [
            row for row in error_rows if row["model_label"] == "foundation_mpa0"
        ]
        cc = sorted(
            float(row["min_C_C_a"])
            for row in foundation_errors
            if row["case"] == "B1_Monovacancy"
        )
        sisi = sorted(
            float(row["min_Si_Si_a"])
            for row in foundation_errors
            if row["case"] == "D_SiGraphene" and row["min_Si_Si_a"] != "nan"
        )
        require(text, f"{cc[0]:.3f}--{cc[-1]:.3f}", "monovacancy C-C range")
        require(text, f"{sisi[0]:.3f}", "minimum Si-Si contact")
        checks += 2

        initial = read_csv(
            first_existing(
                evidence,
                "submission_data/results/initial_snapshot_dft_evidence.csv",
                "review_revision/SNAPSHOT_DFT_EVIDENCE.csv",
            )
        )
        curated_extended = (
            ROOT / "submission_data/results/extended_snapshot_dft_evidence.csv"
        )
        extended = read_csv(
            curated_extended
            if curated_extended.is_file()
            else first_existing(
                evidence,
                "submission_data/results/extended_snapshot_dft_evidence.csv",
                "results/review_revision/production_md_snapshot_dft_analysis/md_snapshot_dft_results.csv",
            )
        )
        usable_extended = [
            row
            for row in extended
            if row["completed"] == "True"
            and row["electronic_converged_marker"] == "True"
            and int(row["final_scf_iteration"]) < int(row["nelm"])
            and row["fatal_error"] == "False"
            and row["usable_dft_energy_ev"]
            and len(row["outcar_sha256"]) == 64
        ]
        usable_initial = [
            row
            for row in initial
            if row["completed"] == "True"
            and row["electronic_converged_marker"] == "True"
            and int(row["final_scf_iteration"]) < int(row["nelm"])
            and row["fatal_error"] == "False"
            and row["forces_readable"] == "True"
            and row["scf_provenance"]
            in {"strict_original", "two_stage_algo_all_rerun"}
            and len(row["outcar_sha256"]) == 64
        ]
        if len(usable_initial) != 9 or len(usable_extended) != 7:
            raise AssertionError("DFT snapshot coverage changed")
        for row in usable_initial:
            require(
                si,
                f"{row['seed']}/{int(row['step'])}",
                f"initial snapshot identifier {row['case']}/{row['step']}",
            )
            require(
                si,
                f"{float(row['dft_energy_without_entropy_ev']):.3f}",
                f"initial snapshot energy {row['case']}/{row['step']}",
            )
        for row in usable_extended:
            require(
                si,
                f"{float(row['usable_dft_energy_ev']):.3f}",
                f"extended snapshot energy {row['structure']}/{row['step']}",
            )
        snapshot_extxyz = first_existing(
            evidence,
            "results/review_revision/high_displacement_mace_eval_strict/high_displacement_dft.extxyz",
            "submission_data/results/high_displacement_dft.extxyz",
        )
        snapshot_extxyz_text = snapshot_extxyz.read_text(encoding="utf-8")
        if sum(line.isdigit() for line in snapshot_extxyz_text.splitlines()) != 9:
            raise AssertionError("high-displacement DFT extxyz does not contain nine frames")
        for row in usable_initial:
            if row["outcar_sha256"] not in snapshot_extxyz_text:
                raise AssertionError(
                    "high-displacement DFT extxyz is missing source hash "
                    f"{row['outcar_sha256']}"
                )
        require(text, "In total, 16", "total converged DFT snapshot count")
        checks += 38

        initial_trajectory_rows = read_csv(
            first_existing(
                evidence,
                "results/review_revision/gpu_analysis/review_md_runs.csv",
                "submission_data/results/initial_md_runs.csv",
            )
        )
        if len(initial_trajectory_rows) != 15 or any(
            row["completed_100ps"] != "True"
            or row["lost_atoms_or_error"] != "False"
            or row["dangerous_builds"] != "0"
            for row in initial_trajectory_rows
        ):
            raise AssertionError("initial trajectory table contains a non-completed run")

        trajectory_rows = read_csv(
            first_existing(
                evidence,
                "results/review_revision/gpu_analysis_20260725_0116/review_md_runs.csv",
                "submission_data/results/production_md_runs.csv",
            )
        )
        if not trajectory_rows or any(
            row["completed_target"] != "True"
            or row["lost_atoms_or_error"] != "False"
            or row["dangerous_builds"] != "0"
            for row in trajectory_rows
        ):
            raise AssertionError("reported trajectory table contains a non-completed run")
        require(text, "four Li atoms per cell", "replicated-cell Li count")
        require(text, r"7.63\times10^{13}", "replicated-cell Li areal density")
        require(text, "thermostat damping time was 0.1 ps", "thermostat damping time")
        require(si, r"\texttt{compute msd}", "LAMMPS displacement command")
        require(si, r"\texttt{com yes}", "Li center-of-mass correction")
        require(
            si,
            "finite-window displacement diagnostic rather than a diffusion estimator",
            "finite-window displacement interpretation",
        )
        checks += 8

        require(text, "DP-GEN concurrent-learning framework", "DP-GEN comparison")
        require(text, "does not apply\na numerical model-deviation threshold", "committee threshold limitation")
        require(text, "does not close a further retraining\ncycle", "open retraining loop")
        require(si, "DP-GEN concurrent learning", "SI concurrent-learning comparison")
        checks += 4

        path_file = ROOT / "submission_data/results/fixed_path_descriptors.csv"
        header = path_file.read_text(encoding="utf-8").splitlines()[0]
        if "barrier" in header.lower() or "path_span_ev" not in header:
            raise AssertionError("curated path descriptor header uses barrier terminology")
        checks += 1

        model_dir = evidence / "submission_data/models"
        if not model_dir.is_dir():
            model_dir = ROOT / "submission_data/models"
        for name, expected_hash in EXPECTED_MODEL_HASHES.items():
            path = model_dir / name
            if not path.is_file() or digest(path) != expected_hash:
                raise AssertionError(f"missing or changed author-trained checkpoint: {name}")
        checks += len(EXPECTED_MODEL_HASHES)
    except (AssertionError, FileNotFoundError, KeyError, ValueError) as exc:
        print(f"FAILED reframed manuscript verification: {exc}")
        return 1

    print(f"PASSED reframed manuscript verification: checks={checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
