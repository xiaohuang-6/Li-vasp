#!/usr/bin/env python3
"""Verify the reframed manuscript's central numerical claims against evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
    args = parser.parse_args()
    evidence = args.evidence_root.resolve()
    text = read_tex_tree(args.tex)
    si = args.si.read_text(encoding="utf-8")
    combined = text + "\n" + si
    checks = 0

    try:
        require(
            text,
            "Local-environment-dependent transferability of a fine-tuned MACE potential",
            "scientific title",
        )
        require(text, "These authors contributed equally", "first-page equal contribution")
        require(text, "Both authors contributed equally", "author-contribution equality")
        if "Declaration of generative AI" in text:
            raise AssertionError("non-required generative-AI declaration remains")
        checks += 4

        report = json.loads(
            (evidence / "data/mace_datasets/li_mace_dataset_report.json").read_text(
                encoding="utf-8"
            )
        )
        grouped = json.loads(
            (
                evidence
                / "data/mace_datasets_grouped/li_mace_grouped_dataset_report.json"
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
        checks += 4

        ads_rows = read_csv(
            evidence
            / "results/review_revision/adsorption_energy_analysis/adsorption_energies.csv"
        )
        ads = {
            row["family"]: float(row["adsorption_energy_ev_per_li"])
            for row in ads_rows
            if row["usable"] == "True"
        }
        expected_families = {
            "A_Perfect",
            "B1_Monovacancy",
            "B2_Divacancy",
            "C_StoneWales",
            "D_SiGraphene",
        }
        if set(ads) != expected_families:
            raise AssertionError("adsorption evidence does not cover five usable families")
        require(text, f"{ads['A_Perfect']:.3f} eV", "pristine adsorption")
        require(text, f"{ads['C_StoneWales']:+.3f} eV", "Stone-Wales adsorption")
        deltas = {
            family: ads["A_Perfect"] - ads[family]
            for family in ("B1_Monovacancy", "B2_Divacancy", "D_SiGraphene")
        }
        require(
            text,
            f"{deltas['B1_Monovacancy']:.3f} and {deltas['D_SiGraphene']:.3f} eV",
            "monovacancy and Si4 adsorption changes",
        )
        require(
            text,
            f"{deltas['B2_Divacancy']:.3f} eV",
            "divacancy adsorption change",
        )
        span = max(ads.values()) - min(ads.values())
        require(text, f"{span:.3f} eV", "adsorption span")
        checks += 7

        mace_rows = read_csv(
            evidence
            / "results/review_revision/gpu_analysis_20260725_0116/mace_eval_summary.csv"
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

        snapshot_rows = read_csv(
            evidence
            / "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/all_models_snapshot_force_summary.csv"
        )
        expected_snapshot = {
            ("foundation_mpa0", "ALL"): 710,
            ("foundation_mpa0", "B1_Monovacancy"): 1149,
            ("foundation_mpa0", "D_SiGraphene"): 310,
            ("grouped_e0", "ALL"): 646,
            ("grouped_e0", "B1_Monovacancy"): 1107,
            ("grouped_e0", "D_SiGraphene"): 114,
        }
        for (model, group), expected in expected_snapshot.items():
            row = row_by(snapshot_rows, model_label=model, group=group)
            actual = round(float(row["force_rmse_mev_a_frame_rms"]))
            if actual != expected:
                raise AssertionError(
                    f"snapshot force RMSE changed for {model}/{group}: {actual}"
                )
        for snippet, label in (
            ("from 710 to 646 meV", "all-snapshot force RMSE change"),
            ("1149 meV", "foundation monovacancy snapshot force RMSE"),
            ("310 meV", "foundation Si4 snapshot force RMSE"),
            ("1107 meV", "fine-tuned monovacancy snapshot force RMSE"),
            ("114 meV", "fine-tuned Si4 snapshot force RMSE"),
        ):
            require(text, snippet, label)
        require(text, "a 63\\% improvement", "Si4 percentage improvement")
        require(text, "a 4\\% improvement", "monovacancy percentage improvement")
        checks += 8

        error_rows = read_csv(
            evidence
            / "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/all_models_snapshot_force_errors.csv"
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

        initial = read_csv(evidence / "review_revision/SNAPSHOT_DFT_EVIDENCE.csv")
        extended = read_csv(
            evidence
            / "results/review_revision/production_md_snapshot_dft_analysis/md_snapshot_dft_results.csv"
        )
        usable_extended = [
            row
            for row in extended
            if row["completed"] == "True"
            and row["electronic_converged_marker"] == "True"
            and row["fatal_error"] == "False"
            and row["usable_dft_energy_ev"]
        ]
        if len(initial) != 9 or len(usable_extended) != 7:
            raise AssertionError("DFT snapshot coverage changed")
        require(text, "In total, 16", "total converged DFT snapshot count")
        checks += 3

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
    except (AssertionError, FileNotFoundError, KeyError) as exc:
        print(f"FAILED reframed manuscript verification: {exc}")
        return 1

    print(f"PASSED reframed manuscript verification: checks={checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
