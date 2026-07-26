#!/usr/bin/env python3
"""Verify high-risk manuscript numbers against current local evidence files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPO_ROOT
TEX_PATH = REPO_ROOT / "manuscript/li_mace_graphene_draft.tex"


def display_path(path: Path) -> Path:
    for root in (REPO_ROOT, EVIDENCE_ROOT):
        try:
            return path.relative_to(root)
        except ValueError:
            pass
    return path


def read_text(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing file: {display_path(path)}")
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing file: {display_path(path)}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt(value: str | float, ndigits: int) -> str:
    return f"{float(value):.{ndigits}f}"


def assert_true(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def contains(text: str, snippet: str, label: str) -> None:
    if snippet not in text:
        raise AssertionError(f"missing manuscript text for {label}: {snippet!r}")


def absent(text: str, snippet: str, label: str) -> None:
    if snippet in text:
        raise AssertionError(f"forbidden manuscript text for {label}: {snippet!r}")


def rows_by(rows: list[dict[str, str]], *keys: str) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def label_family(family: str) -> str:
    return {
        "A_Perfect": "Pristine graphene",
        "B1_Monovacancy": "Monovacancy graphene",
        "B2_Divacancy": "Divacancy graphene",
        "C_StoneWales": "Stone--Wales graphene",
        "D_SiGraphene": "Si$_4$--graphene motif",
    }[family]


def label_path_endpoint(endpoint: str) -> str:
    return {
        "prior_li_xy": "initial Li",
        "hollow_C3": "hollow C$_3$",
        "bridge_C_C": "C--C bridge",
        "top_central_C": "top C",
        "top_offset_C": "offset top C",
    }[endpoint]


def check_author_and_dataset(text: str) -> int:
    n_checks = 0
    contains(text, r"\author{Yuhan Sun$^1$ and Xiao Huang$^{2,*}$}", "author names")
    n_checks += 1
    contains(
        text,
        r"\textit{$^1$University of Waterloo, Waterloo, ON N2L 3G1, Canada;\\",
        "first-author affiliation",
    )
    n_checks += 1

    report = read_json(EVIDENCE_ROOT / "data/mace_datasets/li_mace_dataset_report.json")
    grouped = read_json(EVIDENCE_ROOT / "data/mace_datasets_grouped/li_mace_grouped_dataset_report.json")
    relax_frames = sum(item["frames"] for item in report["extxyz"])
    sp_frames = sum(item["frames"] for item in report["outcars"])
    contains(text, f"contains {report['n_frames']} spin-polarized VASP frames", "abstract frame count")
    contains(text, f"contains {report['n_frames']} frames: {relax_frames} frames", "dataset total")
    contains(text, f"and {sp_frames} fixed-geometry site/path", "fixed-geometry count")
    n_checks += 3
    original = report["frame_counts"]
    contains(
        text,
        f"contained {original['train']} training frames, {original['valid']} validation frames, "
        f"and {original['test']} held-out test frames",
        "original split counts",
    )
    n_checks += 1
    grouped_counts = grouped["frame_counts"]
    contains(
        text,
        f"contains {grouped_counts['train']} training frames, {grouped_counts['valid']} validation frames, "
        f"and {grouped_counts['test']} test frames",
        "grouped split counts",
    )
    assert_true(grouped.get("leakage_free") is True, "grouped split is not leakage_free")
    n_checks += 2
    return n_checks


def check_mace_errors(text: str) -> int:
    n_checks = 0
    rows = rows_by(
        read_csv(EVIDENCE_ROOT / "results/review_revision/gpu_analysis_20260725_0116/mace_eval_summary.csv"),
        "model_label",
        "split",
        "family",
    )

    def row(model: str, split: str, family: str) -> dict[str, str]:
        key = (model, split, family)
        assert_true(key in rows, f"missing MACE summary row: {key}")
        return rows[key]

    foundation_test = row("foundation_mpa0", "test", "ALL")
    fine_test = row("finetuned_3060ti", "test", "ALL")
    fine_d_test = row("finetuned_3060ti", "test", "D_SiGraphene")
    contains(
        text,
        f"from {fmt(foundation_test['force_rmse_mev_a_frame_rms'], 1)} to "
        f"{fmt(fine_test['force_rmse_mev_a_frame_rms'], 1)} meV \\AA$^{{-1}}$",
        "same-workflow force reduction",
    )
    contains(
        text,
        f"Si$_4$--graphene energy RMSE of {fmt(fine_d_test['energy_rmse_mev_atom'], 1)} meV atom$^{{-1}}$",
        "Si4 energy RMSE limitation",
    )
    n_checks += 2

    table_checks = [
        ("foundation_mpa0", "test", "ALL", "Foundation, test all"),
        ("finetuned_3060ti", "train", "ALL", "Fine-tuned, training all"),
        ("finetuned_3060ti", "valid", "ALL", "Fine-tuned, validation all"),
        ("finetuned_3060ti", "test", "ALL", "Fine-tuned, test all"),
        ("finetuned_3060ti", "test", "A_Perfect", "Fine-tuned test: pristine graphene"),
        ("finetuned_3060ti", "test", "B1_Monovacancy", "Fine-tuned test: monovacancy graphene"),
        ("finetuned_3060ti", "test", "B2_Divacancy", "Fine-tuned test: divacancy graphene"),
        ("finetuned_3060ti", "test", "C_StoneWales", "Fine-tuned test: Stone--Wales graphene"),
        ("finetuned_3060ti", "test", "D_SiGraphene", "Fine-tuned test: Si$_4$--graphene motif"),
    ]
    for model, split, family, label in table_checks:
        current = row(model, split, family)
        snippet = (
            f"{label} & {fmt(current['energy_rmse_mev_atom'], 1)} "
            f"& {fmt(current['force_rmse_mev_a_frame_rms'], 1)} \\\\"
        )
        contains(text, snippet, f"MACE table row {label}")
        n_checks += 1

    committee = read_csv(EVIDENCE_ROOT / "results/review_revision/gpu_analysis_20260725_0116/committee_summary.csv")
    force_values = [fmt(row["valid_force_rmse_mev_a"], 1) for row in committee]
    contains(
        text,
        f"internal validation force metrics of {force_values[0]}, {force_values[1]}, "
        f"and {force_values[2]} meV \\AA$^{{-1}}$",
        "committee validation force RMSEs",
    )
    n_checks += 1

    log = read_text(
        EVIDENCE_ROOT
        / "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/logs/agent_grouped_e0_finetune.log"
    )
    assert_true("Loaded Stage one model from epoch 224 for evaluation" in log, "missing grouped-E0 stage-one log")
    assert_true("Loaded Stage two model from epoch 298 for evaluation" in log, "missing grouped-E0 stage-two log")
    stage_one = log.split("Loaded Stage one model from epoch 224 for evaluation", 1)[1]
    stage_one = stage_one.split("Loaded Stage two model from epoch 298 for evaluation", 1)[0]
    expected_config_types = [
        "SP_A_Perfect_cell_center_Default",
        "SP_B1_Monovacancy_bridge_C_C_Default",
        "SP_B2_Divacancy_bridge_C_C_Default",
        "SP_C_StoneWales_cell_center_Default",
        "SP_D_SiGraphene_bridge_C_C_Default",
    ]
    grouped_values: list[str] = []
    for config_type in expected_config_types:
        match = re.search(
            rf"\|\s*{re.escape(config_type)}\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|",
            stage_one,
        )
        assert_true(match is not None, f"missing grouped-E0 stage-one row: {config_type}")
        grouped_values.append(fmt(match.group(2), 1))
    contains(text, "first-stage grouped-E0 checkpoint", "grouped-E0 stage-one source wording")
    contains(
        text,
        "family force RMSEs of "
        f"{grouped_values[0]}, {grouped_values[1]}, {grouped_values[2]}, "
        f"{grouped_values[3]}, and {grouped_values[4]} meV \\AA$^{{-1}}$",
        "grouped-E0 stage-one family force RMSEs",
    )
    n_checks += 4
    return n_checks


def check_adsorption_and_paths(text: str) -> int:
    n_checks = 0
    ads = read_csv(EVIDENCE_ROOT / "results/review_revision/adsorption_energy_analysis/adsorption_energies.csv")
    assert_true(all(row["usable"] == "True" for row in ads), "not all adsorption energies are usable")
    by_family = {row["family"]: row for row in ads}
    min_ads = min(float(row["adsorption_energy_ev_per_li"]) for row in ads)
    max_ads = max(float(row["adsorption_energy_ev_per_li"]) for row in ads)
    contains(text, f"from {fmt(min_ads, 2)} to +{fmt(max_ads, 2)} eV per Li", "abstract adsorption range")
    contains(text, f"$E_{{\\mathrm{{ads}}}}={fmt(min_ads, 3)}$ to {fmt(max_ads, 3)} eV per Li", "adsorption exact range")
    n_checks += 2
    table_labels = {
        "A_Perfect": "Pristine graphene",
        "B1_Monovacancy": "Monovacancy graphene",
        "B2_Divacancy": "Divacancy graphene",
        "C_StoneWales": "Stone--Wales graphene",
        "D_SiGraphene": "Si$_4$--graphene motif",
    }
    for family, label in table_labels.items():
        value = fmt(by_family[family]["adsorption_energy_ev_per_li"], 3)
        contains(text, f"{label} & {value} \\\\", f"adsorption table {family}")
        n_checks += 1

    paths = read_csv(EVIDENCE_ROOT / "results/two_day_rush/path_barriers.csv")
    spans = [float(row["barrier_from_path_min_ev"]) for row in paths]
    contains(text, f"fixed-geometry path spans of {fmt(min(spans), 3)}--{fmt(max(spans), 3)} eV", "path span range")
    n_checks += 1
    for row in paths:
        system = label_family(row["family"])
        path = f"{label_path_endpoint(row['path_start'])} $\\rightarrow$ {label_path_endpoint(row['path_end'])}"
        span = fmt(row["barrier_from_path_min_ev"], 3)
        delta = fmt(row["delta_e_end_minus_start_ev"], 3)
        contains(text, f"{system} & {path} & {span} & {delta} \\\\", f"path table {row['family']} {row['path_id']}")
        n_checks += 1
    return n_checks


def check_md_and_snapshots(text: str) -> int:
    n_checks = 0
    md_rows = read_csv(EVIDENCE_ROOT / "results/review_revision/gpu_analysis_20260725_0116/review_md_runs.csv")
    assert_true(len(md_rows) == 18, "follow-up MD row count is not 18")
    assert_true(all(row["completed_target"] == "True" for row in md_rows), "not all follow-up MD runs completed target")
    assert_true(all(row["lost_atoms_or_error"] == "False" for row in md_rows), "follow-up MD has lost atoms or errors")
    assert_true(all(row["dangerous_builds"] == "0" for row in md_rows), "follow-up MD has dangerous builds")
    contains(text, "18/18 target-length trajectories", "follow-up MD completion count")
    n_checks += 5

    def md_group(family: str, model_family: str) -> list[dict[str, str]]:
        rows = [row for row in md_rows if row["structure"] == family and row["model_family"] == model_family]
        assert_true(len(rows) == 3, f"expected 3 MD rows for {family}/{model_family}, got {len(rows)}")
        return rows

    all_msd = [float(row["final_msd_xy_a2"]) for row in md_rows]
    contains(text, f"span {fmt(min(all_msd), 1)}--{fmt(max(all_msd), 1)} \\AA$^2$", "all follow-up MSD range")
    n_checks += 1
    md_specs = [
        ("A_Perfect", "finetuned_reference", "Pristine graphene & Reference model", "500"),
        ("B1_Monovacancy", "committee_model", "Monovacancy graphene & Committee models", "200"),
        ("B2_Divacancy", "committee_model", "Divacancy graphene & Committee models", "200"),
        ("C_StoneWales", "finetuned_reference", "Stone--Wales graphene & Reference model", "500"),
        ("D_SiGraphene", "committee_model", "Si$_4$--graphene motif & Committee models", "200"),
        ("D_SiGraphene", "finetuned_reference", "Si$_4$--graphene motif & Reference model", "500"),
    ]
    ranges: dict[tuple[str, str], tuple[float, float]] = {}
    for family, model_family, label, ps in md_specs:
        rows = md_group(family, model_family)
        values = [float(row["final_msd_xy_a2"]) for row in rows]
        low, high = min(values), max(values)
        ranges[(family, model_family)] = (low, high)
        contains(
            text,
            f"{label} & {ps} & 3/3 & Stable completion; final MSD$_{{xy}}$ = "
            f"{fmt(low, 1)}--{fmt(high, 1)} \\AA$^2$ \\\\",
            f"MD table {family}/{model_family}",
        )
        n_checks += 1
    d_ref_low, d_ref_high = ranges[("D_SiGraphene", "finetuned_reference")]
    d_com_low, d_com_high = ranges[("D_SiGraphene", "committee_model")]
    contains(
        text,
        f"they span {fmt(d_ref_low, 1)}--{fmt(d_ref_high, 1)} \\AA$^2$ in the three 500 ps reference-model runs",
        "Si4 reference MSD range",
    )
    contains(
        text,
        f"and {fmt(d_com_low, 1)}--{fmt(d_com_high, 1)} \\AA$^2$ in the three 200 ps committee-model runs",
        "Si4 committee MSD range",
    )
    contains(text, f"differ by {fmt(d_ref_high - d_ref_low, 1)} \\AA$^2$", "Si4 reference MSD spread")
    contains(text, f"differ by {fmt(d_com_high - d_com_low, 1)} \\AA$^2$", "Si4 committee MSD spread")
    n_checks += 4

    dft_rows = read_csv(EVIDENCE_ROOT / "review_revision/SNAPSHOT_DFT_EVIDENCE.csv")
    assert_true(len(dft_rows) == 9, "snapshot DFT row count is not 9")
    assert_true(all(row["completed"] == "True" for row in dft_rows), "not all snapshot DFT rows completed")
    assert_true(all(row["electronic_converged_marker"] == "True" for row in dft_rows), "not all snapshot DFT rows converged")
    assert_true(all(row["fatal_error"] == "False" for row in dft_rows), "snapshot DFT row has fatal marker")
    assert_true(all(row["forces_readable"] == "True" for row in dft_rows), "snapshot DFT forces are not all readable")
    n_checks += 5
    for row in dft_rows:
        case_label = "Si$_4$--graphene" if row["case"] == "D_SiGraphene" else "Monovacancy graphene"
        snippet = (
            f"{case_label} & {row['seed']}/{int(row['step'])} & {fmt(row['time_ps'], 1)} "
            f"& {fmt(row['msd_xy_a2'], 1)} & {fmt(row['dft_energy_without_entropy_ev'], 3)} &"
        )
        contains(text, snippet, f"snapshot DFT table {row['case']} {row['seed']}/{row['step']}")
        n_checks += 1

    force_summary = rows_by(
        read_csv(
            EVIDENCE_ROOT
            / "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/all_models_snapshot_force_summary.csv"
        ),
        "model_label",
        "group",
    )

    def force(model: str, group: str) -> float:
        key = (model, group)
        assert_true(key in force_summary, f"missing snapshot-force summary row: {key}")
        return float(force_summary[key]["force_rmse_mev_a_frame_rms"])

    contains(text, f"force RMSE of {fmt(force('foundation_mpa0', 'ALL'), 0)} meV \\AA$^{{-1}}$", "foundation all snapshot force")
    contains(text, f"including {fmt(force('foundation_mpa0', 'B1_Monovacancy'), 0)} meV \\AA$^{{-1}}$", "foundation B1 snapshot force")
    contains(text, f"and {fmt(force('foundation_mpa0', 'D_SiGraphene'), 0)} meV \\AA$^{{-1}}$", "foundation D snapshot force")
    contains(text, f"to {fmt(force('grouped_e0', 'D_SiGraphene'), 0)} meV \\AA$^{{-1}}$", "grouped-E0 D snapshot force")
    contains(text, f"remains {fmt(force('grouped_e0', 'B1_Monovacancy'), 0)} meV \\AA$^{{-1}}$", "grouped-E0 B1 snapshot force")
    contains(text, f"remains {fmt(force('grouped_e0', 'ALL'), 0)} meV \\AA$^{{-1}}$", "grouped-E0 all snapshot force")
    n_checks += 6

    force_errors = [
        row
        for row in read_csv(
            EVIDENCE_ROOT
            / "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/all_models_snapshot_force_errors.csv"
        )
        if row["model_label"] == "foundation_mpa0"
    ]
    b1_cc = sorted(
        float(row["min_C_C_a"]) for row in force_errors if row["case"] == "B1_Monovacancy" and row["min_C_C_a"] != "nan"
    )
    si_si = sorted(
        float(row["min_Si_Si_a"]) for row in force_errors if row["case"] == "D_SiGraphene" and row["min_Si_Si_a"] != "nan"
    )
    contains(
        text,
        f"minimum C--C contacts of {fmt(b1_cc[0], 3)}, {fmt(b1_cc[1], 3)}, and {fmt(b1_cc[2], 3)} \\AA{{}}",
        "monovacancy contact distances",
    )
    contains(text, f"minimum Si--Si contact of {fmt(si_si[0], 3)} \\AA{{}}", "Si4 contact distance")
    n_checks += 2

    production_status = read_text(
        EVIDENCE_ROOT / "results/review_revision/production_md_snapshot_dft_analysis/MD_SNAPSHOT_DFT_STATUS.md"
    )
    assert_true("- Completed snapshot checks: 1/7." in production_status, "production snapshot DFT completed count changed")
    assert_true(
        "- Snapshot checks with usable converged energies: 1/7." in production_status,
        "production snapshot DFT usable count changed",
    )
    contains(
        text,
        "These rows are deliberately not presented as validation of the later 200--500 ps production set",
        "production snapshot DFT gate",
    )
    absent(text, "D_SiGraphene_seed20260427_step057000", "single production snapshot should not be in manuscript")
    n_checks += 4
    return n_checks


def check_scheduler_gates_and_language(text: str) -> int:
    n_checks = 0
    fast = read_text(EVIDENCE_ROOT / "results/review_revision/neb_fast_analysis/REVIEW_NEB_STATUS.md")
    full = read_text(EVIDENCE_ROOT / "results/review_revision/neb_analysis_current/REVIEW_NEB_STATUS.md")
    assert_true("- Jobs reporting VASP ionic convergence: 0/5." in fast, "fast NEB convergence count changed")
    assert_true("- Jobs reporting VASP ionic convergence: 0/10." in full, "full NEB convergence count changed")
    assert_true("- Jobs with fatal error markers: 1/10." in full, "full NEB fatal count changed")
    contains(text, "No completed climbing-image NEB result is used in the present analysis", "NEB exclusion")
    contains(text, "not as migration barriers", "path scans are not barriers")
    contains(text, "CI-NEB barriers and converged diffusion statistics are excluded from the quantitative claims", "abstract kinetic exclusion")
    for phrase in (
        "production-trajectory validation claim",
        "reported diffusion coefficient",
        "reported migration barrier",
    ):
        absent(text, phrase, f"overclaim phrase {phrase}")
    n_checks += 10
    return n_checks


def main() -> int:
    global EVIDENCE_ROOT

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tex",
        type=Path,
        default=TEX_PATH,
        help="Manuscript file to verify.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=EVIDENCE_ROOT,
        help="Repository/evidence root containing ignored data and results files.",
    )
    args = parser.parse_args()

    EVIDENCE_ROOT = args.evidence_root.resolve()

    try:
        text = read_text(args.tex)
        checks = 0
        checks += check_author_and_dataset(text)
        checks += check_mace_errors(text)
        checks += check_adsorption_and_paths(text)
        checks += check_md_and_snapshots(text)
        checks += check_scheduler_gates_and_language(text)
    except AssertionError as exc:
        print(f"FAILED manuscript numeric verification: {exc}", file=sys.stderr)
        return 1

    print(f"PASSED manuscript numeric verification: checks={checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
