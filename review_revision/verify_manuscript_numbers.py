#!/usr/bin/env python3
"""Verify high-risk manuscript numbers against current local evidence files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPO_ROOT
CURATED_ROOT = REPO_ROOT / "submission_data"
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
    contains(
        text,
        r"\title{Validation-first DFT--MACE screening of local lithium energetics in pristine and defective graphene and a Si$_4$--graphene motif}",
        "validation-first manuscript title",
    )
    n_checks += 1
    contains(text, r"\label{tab:validation_gates}", "operational validation-gate table")
    n_checks += 1
    contains(text, r"\author{Yuhan Sun$^1$ and Xiao Huang$^{2,*}$}", "author names")
    n_checks += 1
    contains(
        text,
        r"\textit{$^1$University of Waterloo, Waterloo, ON N2L 3G1, Canada;\\",
        "first-author affiliation",
    )
    n_checks += 1
    contains(
        text,
        r"\textbf{Keywords:} machine-learned interatomic potentials; MACE; lithium adsorption; defective graphene; density functional theory; data leakage; AI for materials",
        "submission keywords",
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
    split_policy = grouped.get("split_policy", {})
    assert_true(
        split_policy.get("grouped_by") == "relax trajectories and path-image groups",
        "grouped split policy changed",
    )
    assert_true(split_policy.get("relax_split") == "train", "relaxation trajectories are not all in training")
    for split in ("valid", "test"):
        family_counts = grouped.get("split_family_counts", {}).get(split, {})
        assert_true(
            set(family_counts) == {
                "A_Perfect",
                "B1_Monovacancy",
                "B2_Divacancy",
                "C_StoneWales",
                "D_SiGraphene",
            }
            and all(count == 1 for count in family_counts.values()),
            f"grouped {split} split is not one configuration per family",
        )
    contains(
        text,
        "keeps every relaxation trajectory in training, keeps all images from each fixed path in one group, "
        "sorts the remaining site/path groups within each structural family, and assigns those groups by a "
        "deterministic 8:1:1 train/validation/test cycle",
        "grouped split assignment policy",
    )
    contains(
        text,
        "The validation and test sets each contain one configuration from each of the five families",
        "grouped held-out family counts",
    )
    n_checks += 6
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
    contains(text, "first-stage grouped-\\(E_0\\) checkpoint", "grouped-E0 stage-one source wording")
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
    assert_true("- Completed snapshot checks: 2/7." in production_status, "production snapshot DFT completed count changed")
    assert_true(
        "- Snapshot checks with usable converged energies: 2/7." in production_status,
        "production snapshot DFT usable count changed",
    )
    contains(
        text,
        "These rows are deliberately not presented as validation of the later 200--500 ps extended diagnostic set",
        "production snapshot DFT gate",
    )
    absent(text, "D_SiGraphene_seed20260427_step057000", "production snapshot should not be in manuscript")
    absent(text, "D_SiGraphene_seed20260427_step500000", "production snapshot should not be in manuscript")
    n_checks += 5
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


def check_method_provenance(text: str) -> int:
    n_checks = 0

    structure_builder = read_text(EVIDENCE_ROOT / "build_defect_structures.py")
    for snippet in (
        'default=(5, 5, 1)',
        'parser.add_argument("--a", type=float, default=2.46',
        'parser.add_argument("--vacuum", type=float, default=15.0)',
    ):
        assert_true(snippet in structure_builder, f"structure-builder default changed: {snippet}")
        n_checks += 1
    structure_summary = json.loads(
        read_text(EVIDENCE_ROOT / "structures/vasp/structure_summary.json")
    )
    expected_structures = [
        ("C50Li", 51),
        ("C49Li", 50),
        ("C48Li", 49),
        ("C50Li", 51),
        ("C50LiSi4", 55),
    ]
    assert_true(
        [(record["formula"], record["natoms"]) for record in structure_summary]
        == expected_structures,
        "initial structure formulas or atom counts changed",
    )
    assert_true(
        all(float(record["cell"][2][2]) == 30.0 for record in structure_summary),
        "initial structure cell height changed",
    )
    initial_poscars = sorted((EVIDENCE_ROOT / "structures/vasp").glob("POSCAR_*.vasp"))
    assert_true(len(initial_poscars) == 5, "initial POSCAR count is not 5")
    assert_true(
        all("Selective dynamics" not in read_text(path) for path in initial_poscars),
        "an initial POSCAR contains selective-dynamics constraints",
    )
    n_checks += 4
    for snippet, label in (
        (
            r"A graphene lattice parameter of 2.46 \AA{} and a 5 $\times$ 5 supercell",
            "initial graphene lattice and supercell",
        ),
        (
            r"The 30.0 \AA{} cell height places 15.0 \AA{} of vacuum on each side",
            "initial slab vacuum",
        ),
        (
            r"The resulting initial formulas were C$_{50}$Li, C$_{49}$Li, C$_{48}$Li, "
            r"C$_{50}$Li, and C$_{50}$LiSi$_4$",
            "initial structure formulas",
        ),
        (
            r"four non-substitutional Si atoms above the intact C$_{50}$ sheet",
            "non-substitutional Si4 construction",
        ),
    ):
        contains(text, snippet, label)
        n_checks += 1

    vasp_outcar = read_text(EVIDENCE_ROOT / "dft_outputs/A_Perfect/OUTCAR")
    assert_true("vasp.5.4.1" in vasp_outcar, "VASP version changed")
    contains(text, "VASP 5.4.1", "VASP version")
    n_checks += 2
    si_vasp_outcar = read_text(EVIDENCE_ROOT / "dft_outputs/D_SiGraphene/OUTCAR")
    for snippet, source in (
        ("TITEL  = PAW_PBE C 08Apr2002", vasp_outcar),
        ("TITEL  = PAW_PBE Li_sv 10Sep2004", vasp_outcar),
        ("TITEL  = PAW_PBE Si 05Jan2001", si_vasp_outcar),
    ):
        assert_true(snippet in source, f"PAW dataset provenance changed: {snippet}")
        n_checks += 1
    contains(
        text,
        "PAW\\_PBE datasets as C (08Apr2002), Li\\_sv (10Sep2004), and Si (05Jan2001)",
        "PAW dataset labels",
    )
    n_checks += 1
    label_incar = read_text(EVIDENCE_ROOT / "dft_outputs/A_Perfect/INCAR")
    for snippet in (
        "PREC = Accurate",
        "LREAL = Auto",
        "ALGO = Normal",
        "NELM = 120",
        "IBRION = 2",
        "ISIF = 2",
        "NSW = 100",
        "EDIFF = 1E-5",
        "EDIFFG = -0.02",
    ):
        assert_true(snippet in label_incar, f"DFT-label input changed: {snippet}")
        n_checks += 1
    contains(
        text,
        "PREC = Accurate, LREAL = Auto, ALGO = Normal, NELM = 120",
        "DFT-label numerical settings",
    )
    contains(
        text,
        "relaxed without selective-dynamics constraints at fixed lattice vectors using "
        "IBRION = 2, ISIF = 2, NSW = 100",
        "fixed-cell ionic relaxation",
    )
    contains(
        text,
        "Single-point site and path-scan labels used IBRION = -1, NSW = 0",
        "fixed-geometry labeling",
    )
    n_checks += 3

    adsorption_incars = sorted(
        (EVIDENCE_ROOT / "review_revision/adsorption_energy_jobs").glob(
            "*_sp/INCAR"
        )
    )
    slab_adsorption_incars = [
        path for path in adsorption_incars if path.parent.name != "Li_atom_sp"
    ]
    assert_true(len(slab_adsorption_incars) == 10, "adsorption slab INCAR count is not 10")
    for snippet in (
        "IVDW = 12",
        "LDIPOL = .TRUE.",
        "IDIPOL = 3",
        "LREAL = .FALSE.",
        "NELM = 180",
        "IBRION = -1",
        "NSW = 0",
    ):
        assert_true(
            all(snippet in read_text(path) for path in slab_adsorption_incars),
            f"adsorption slab input changed: {snippet}",
        )
        n_checks += 1
    li_atom_incar = read_text(
        EVIDENCE_ROOT / "review_revision/adsorption_energy_jobs/Li_atom_sp/INCAR"
    )
    assert_true("IVDW" not in li_atom_incar, "isolated Li reference unexpectedly uses D3")
    assert_true("LDIPOL" not in li_atom_incar, "isolated Li reference unexpectedly uses a dipole correction")
    li_atom_kpoints = read_text(
        EVIDENCE_ROOT / "review_revision/adsorption_energy_jobs/Li_atom_sp/KPOINTS"
    )
    assert_true("\nGamma\n1 1 1\n" in li_atom_kpoints, "isolated Li k-point mesh changed")
    contains(
        text,
        "DFT-D3 method with Becke--Johnson damping (PBE-D3(BJ); IVDW = 12)",
        "D3(BJ) adsorption method",
    )
    contains(
        text,
        "slab dipole correction (LDIPOL = .TRUE., IDIPOL = 3)",
        "adsorption dipole correction",
    )
    n_checks += 6

    reference_log = read_text(
        EVIDENCE_ROOT
        / "local_3060ti_finetune_pack/logs/local_li_mace_v1/li_mace_v1_3060ti_run-20260427.log"
    )
    for snippet in (
        "MACE version: 0.3.15",
        "Batch size: 2",
        "Learning rate: 0.0005",
        "Stage Two (after 225 epochs)",
        "Epoch 299:",
    ):
        assert_true(snippet in reference_log, f"reference MACE provenance changed: {snippet}")
        n_checks += 1
    reference_script = read_text(EVIDENCE_ROOT / "local_3060ti_finetune_pack/run_finetune.sh")
    assert_true('DEFAULT_DTYPE="${DEFAULT_DTYPE:-float64}"' in reference_script, "reference dtype changed")
    contains(text, "This MACE 0.3.15 run used double precision, batch size 2, 300 epochs", "reference training settings")
    contains(text, r"initial learning rate of \(5\times 10^{-4}\)", "reference learning rate")
    n_checks += 3

    committee_log = read_text(
        EVIDENCE_ROOT
        / "incoming_gpu_results/reviewer_5080_20260721/extracted/local_5080_reviewer_gpu_pack/logs/review_revision/li_mace_review_seed20260427/li_mace_review_seed20260427_run-20260427.log"
    )
    for snippet in (
        "MACE version: 0.3.16",
        "Batch size: 4",
        "Learning rate: 0.001",
        "Stage Two (after 225 epochs)",
    ):
        assert_true(snippet in committee_log, f"committee MACE provenance changed: {snippet}")
        n_checks += 1
    committee_script = read_text(
        EVIDENCE_ROOT / "local_5080_reviewer_gpu_pack/scripts/run_02_committee_train.sh"
    )
    assert_true('DEFAULT_DTYPE="${DEFAULT_DTYPE:-float32}"' in committee_script, "committee dtype changed")
    n_checks += 1

    grouped_log = read_text(
        EVIDENCE_ROOT
        / "results/review_revision/md_snapshot_mace_eval_5080_grouped_e0_20260725_2309/logs/agent_grouped_e0_finetune.log"
    )
    for snippet in (
        "MACE version: 0.3.16",
        "dtype: float64",
        "Batch size: 4",
        "Learning rate: 0.001",
        "Stage Two (after 225 epochs)",
        "Epoch 299:",
        "Radial cutoff: 6.0 A",
        "2 layers, each with correlation order: 3",
        "Estimating E0s using foundation model on 263 configurations with 3 elements",
        "Rank of system: 3/3",
        "Element 3: foundation E0 = -0.297547 eV, correction = -2.973771 eV, new E0 = -3.271318 eV",
        "Element 6: foundation E0 = -1.261735 eV, correction = 0.015411 eV, new E0 = -1.246324 eV",
        "Element 14: foundation E0 = -0.826390 eV, correction = -0.453955 eV, new E0 = -1.280346 eV",
    ):
        assert_true(snippet in grouped_log, f"grouped-E0 provenance changed: {snippet}")
        n_checks += 1
    contains(
        text,
        r"MACE 0.3.16, batch size 4, 300 epochs, an initial learning rate of \(10^{-3}\)",
        "revision training settings",
    )
    contains(text, r"6.0 \AA{} radial cutoff, two interaction layers", "MACE cutoff and layers")
    contains(text, r"correlation order 3, and spherical harmonics through \(l=3\)", "MACE angular settings")
    contains(
        text,
        "foundation-model predictions over all 263 grouped training configurations, a full-rank (3/3) elemental correction fit",
        "grouped-E0 estimation method",
    )
    contains(
        text,
        "baseline offsets of -3.271318, -1.246324, and -1.280346 eV for Li, C, and Si",
        "grouped-E0 baseline offsets",
    )
    n_checks += 5

    snapshot_script = read_text(EVIDENCE_ROOT / "review_revision/prepare_md_snapshot_dft_checks.py")
    for snippet in (
        "ENCUT = 520",
        "EDIFF = 1E-6",
        "ISMEAR = 0",
        "SIGMA = 0.05",
        "PREC = Accurate",
        "LREAL = .FALSE.",
        "ALGO = Normal",
        "IBRION = -1",
        "NSW = 0",
        "ISPIN = 2",
        "ISYM = 0",
        "LASPH = .TRUE.",
        "ADDGRID = .TRUE.",
    ):
        assert_true(snippet in snapshot_script, f"snapshot DFT input provenance changed: {snippet}")
        n_checks += 1
    assert_true("IVDW" not in snapshot_script, "snapshot DFT unexpectedly enables dispersion")
    assert_true("LDIPOL" not in snapshot_script, "snapshot DFT unexpectedly enables dipole correction")
    snapshot_kpoints = read_text(
        EVIDENCE_ROOT / "review_revision/md_snapshot_dft_jobs/D_SiGraphene_seed20260429_step100000/KPOINTS"
    )
    assert_true("\nGamma\n1 1 1\n" in snapshot_kpoints, "snapshot DFT k-point mesh changed")
    snapshot_outcar = read_text(
        EVIDENCE_ROOT / "review_revision/md_snapshot_dft_jobs/D_SiGraphene_seed20260429_step100000/OUTCAR"
    )
    assert_true("LDIPOL =      F" in snapshot_outcar, "snapshot DFT dipole setting changed")
    contains(
        text,
        "These snapshot single points reused the same PAW\\_PBE datasets and used ENCUT = 520 eV",
        "snapshot DFT method",
    )
    contains(
        text,
        "No explicit dispersion or dipole correction was applied to these snapshot stress tests",
        "snapshot DFT correction boundary",
    )
    n_checks += 6

    lammps_driver = read_text(
        EVIDENCE_ROOT
        / "incoming_gpu_results/reviewer_5080_20260725_0116_second/local_5080_reviewer_gpu_pack/logs/A_Perfect_400K_seed20260427_500000steps.driver.log"
    )
    assert_true("LAMMPS (10 Sep 2025)" in lammps_driver, "LAMMPS version changed")
    md_input = read_text(EVIDENCE_ROOT / "review_revision/in.lammps_review_unwrapped_md")
    for snippet in (
        "variable tdamp equal 0.100",
        "fix ensemble all nvt",
        "compute li_msd li msd com yes",
    ):
        assert_true(snippet in md_input, f"MD input provenance changed: {snippet}")
        n_checks += 1
    md_log = read_text(
        EVIDENCE_ROOT
        / "incoming_gpu_results/reviewer_5080_20260725_0116_second/local_5080_reviewer_gpu_pack/review_revision/md_logs/A_Perfect_400K_seed20260427_500000steps.log"
    )
    assert_true("run 10000" in md_log, "production MD equilibration changed")
    contains(text, "LAMMPS (10 September 2025)", "LAMMPS version")
    contains(text, r"10 ps equilibration under a Nos\'e--Hoover NVT thermostat", "MD equilibration")
    contains(text, "0.1 ps damping time", "thermostat damping")
    contains(text, "collective Li center-of-mass drift removal", "MSD drift removal")
    n_checks += 6
    return n_checks


def check_curated_submission(text: str, curated_root: Path) -> int:
    """Verify manuscript claims using only the redistributable package."""

    n_checks = 0

    manifest_path = curated_root / "MANIFEST.sha256"
    manifest_lines = [
        line for line in read_text(manifest_path).splitlines() if line.strip()
    ]
    assert_true(len(manifest_lines) == 24, "curated manifest entry count is not 24")
    n_checks += 1
    for line in manifest_lines:
        try:
            expected, relative = line.split("  ", 1)
        except ValueError as exc:
            raise AssertionError(f"malformed curated manifest line: {line}") from exc
        relative_path = Path(relative)
        assert_true(
            not relative_path.is_absolute() and ".." not in relative_path.parts,
            f"unsafe curated manifest path: {relative}",
        )
        path = curated_root / relative_path
        assert_true(path.is_file(), f"missing curated manifest file: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert_true(actual == expected, f"curated hash mismatch: {relative}")
        n_checks += 1

    original = read_json(curated_root / "datasets/original_split/report.json")
    grouped = read_json(curated_root / "datasets/grouped_split/report.json")
    original_relax = sum(item["frames"] for item in original["extxyz"])
    original_fixed = sum(item["frames"] for item in original["outcars"])
    for report, label in ((original, "original"), (grouped, "grouped")):
        assert_true(report["n_frames"] == 273, f"{label} curated frame count changed")
        n_checks += 1
    assert_true(original_relax == 194, "curated relaxation-frame count changed")
    assert_true(original_fixed == 79, "curated fixed-geometry-frame count changed")
    assert_true(
        original["frame_counts"] == {"train": 211, "valid": 31, "test": 31},
        "curated original split counts changed",
    )
    assert_true(
        grouped["frame_counts"] == {"train": 263, "valid": 5, "test": 5},
        "curated grouped split counts changed",
    )
    assert_true(grouped.get("leakage_free") is True, "curated grouped split is not leakage_free")
    n_checks += 5
    split_policy = grouped.get("split_policy", {})
    assert_true(
        split_policy.get("grouped_by") == "relax trajectories and path-image groups"
        and split_policy.get("relax_split") == "train",
        "curated grouped split policy changed",
    )
    for split in ("valid", "test"):
        family_counts = grouped.get("split_family_counts", {}).get(split, {})
        assert_true(
            len(family_counts) == 5 and all(count == 1 for count in family_counts.values()),
            f"curated grouped {split} split is not one configuration per family",
        )
    contains(
        text,
        "assigns those groups by a deterministic 8:1:1 train/validation/test cycle",
        "curated grouped split assignment",
    )
    contains(
        text,
        "The validation and test sets each contain one configuration from each of the five families",
        "curated grouped held-out family counts",
    )
    n_checks += 5
    contains(text, "contains 273 spin-polarized VASP frames", "curated abstract frame count")
    contains(text, "contains 273 frames: 194 frames", "curated dataset frame count")
    contains(text, "and 79 fixed-geometry site/path", "curated fixed-geometry frame count")
    contains(
        text,
        "contained 211 training frames, 31 validation frames, and 31 held-out test frames",
        "curated original split counts",
    )
    contains(
        text,
        "contains 263 training frames, 5 validation frames, and 5 test frames",
        "curated grouped split counts",
    )
    n_checks += 5

    mace_rows = rows_by(
        read_csv(curated_root / "results/mace_eval_summary.csv"),
        "model_label",
        "split",
        "family",
    )

    def mace_row(model: str, split: str, family: str) -> dict[str, str]:
        key = (model, split, family)
        assert_true(key in mace_rows, f"missing curated MACE summary row: {key}")
        return mace_rows[key]

    foundation_test = mace_row("foundation_mpa0", "test", "ALL")
    fine_test = mace_row("finetuned_3060ti", "test", "ALL")
    fine_d_test = mace_row("finetuned_3060ti", "test", "D_SiGraphene")
    contains(
        text,
        f"from {fmt(foundation_test['force_rmse_mev_a_frame_rms'], 1)} to "
        f"{fmt(fine_test['force_rmse_mev_a_frame_rms'], 1)} meV \\AA$^{{-1}}$",
        "curated same-workflow force reduction",
    )
    contains(
        text,
        f"Si$_4$--graphene energy RMSE of {fmt(fine_d_test['energy_rmse_mev_atom'], 1)} meV atom$^{{-1}}$",
        "curated Si4 energy RMSE",
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
        current = mace_row(model, split, family)
        contains(
            text,
            f"{label} & {fmt(current['energy_rmse_mev_atom'], 1)} "
            f"& {fmt(current['force_rmse_mev_a_frame_rms'], 1)} \\\\",
            f"curated MACE table row {label}",
        )
        n_checks += 1

    committee = read_csv(curated_root / "results/committee_summary.csv")
    assert_true(len(committee) == 3, "curated committee row count is not 3")
    assert_true(all(row["completed"] == "True" for row in committee), "curated committee run is incomplete")
    committee_values = [fmt(row["valid_force_rmse_mev_a"], 1) for row in committee]
    contains(
        text,
        f"internal validation force metrics of {committee_values[0]}, {committee_values[1]}, "
        f"and {committee_values[2]} meV \\AA$^{{-1}}$",
        "curated committee force RMSEs",
    )
    n_checks += 3

    grouped_log = read_text(curated_root / "logs/grouped_e0_training_audit.log")
    grouped_log_snippets = (
        "MACE version: 0.3.16",
        "CUDA version: 12.8, CUDA device: 0",
        "Training set 1/1 [energy: 263",
        "Validation set 1/1 [energy: 5",
        "Test set 1/1 [energy: 5",
        "Estimating E0s using foundation model on 263 configurations with 3 elements",
        "Rank of system: 3/3",
        "Element 3: foundation E0 = -0.297547 eV, correction = -2.973771 eV, new E0 = -3.271318 eV",
        "Element 6: foundation E0 = -1.261735 eV, correction = 0.015411 eV, new E0 = -1.246324 eV",
        "Element 14: foundation E0 = -0.826390 eV, correction = -0.453955 eV, new E0 = -1.280346 eV",
        "Loaded Stage one model from epoch 224 for evaluation",
        "Loaded Stage two model from epoch 298 for evaluation",
    )
    for snippet in grouped_log_snippets:
        assert_true(snippet in grouped_log, f"curated grouped-E0 log changed: {snippet}")
        n_checks += 1
    contains(
        text,
        "foundation-model predictions over all 263 grouped training configurations, a full-rank (3/3) elemental correction fit",
        "curated grouped-E0 method",
    )
    contains(
        text,
        "baseline offsets of -3.271318, -1.246324, and -1.280346 eV for Li, C, and Si",
        "curated grouped-E0 offsets",
    )
    n_checks += 2

    ads = read_csv(curated_root / "results/adsorption_energies.csv")
    assert_true(len(ads) == 5, "curated adsorption row count is not 5")
    assert_true(all(row["usable"] == "True" for row in ads), "curated adsorption result is unusable")
    by_family = {row["family"]: row for row in ads}
    min_ads = min(float(row["adsorption_energy_ev_per_li"]) for row in ads)
    max_ads = max(float(row["adsorption_energy_ev_per_li"]) for row in ads)
    contains(text, f"from {fmt(min_ads, 2)} to +{fmt(max_ads, 2)} eV per Li", "curated adsorption range")
    contains(text, f"$E_{{\\mathrm{{ads}}}}={fmt(min_ads, 3)}$ to {fmt(max_ads, 3)} eV per Li", "curated exact adsorption range")
    n_checks += 4
    adsorption_labels = {
        "A_Perfect": "Pristine graphene",
        "B1_Monovacancy": "Monovacancy graphene",
        "B2_Divacancy": "Divacancy graphene",
        "C_StoneWales": "Stone--Wales graphene",
        "D_SiGraphene": "Si$_4$--graphene motif",
    }
    for family, label in adsorption_labels.items():
        contains(
            text,
            f"{label} & {fmt(by_family[family]['adsorption_energy_ev_per_li'], 3)} \\\\",
            f"curated adsorption table {family}",
        )
        n_checks += 1

    paths = read_csv(curated_root / "results/fixed_path_descriptors.csv")
    assert_true(len(paths) == 10, "curated fixed-path row count is not 10")
    spans = [float(row["barrier_from_path_min_ev"]) for row in paths]
    contains(text, f"fixed-geometry path spans of {fmt(min(spans), 3)}--{fmt(max(spans), 3)} eV", "curated path span")
    n_checks += 2
    for row in paths:
        system = label_family(row["family"])
        path = f"{label_path_endpoint(row['path_start'])} $\\rightarrow$ {label_path_endpoint(row['path_end'])}"
        contains(
            text,
            f"{system} & {path} & {fmt(row['barrier_from_path_min_ev'], 3)} "
            f"& {fmt(row['delta_e_end_minus_start_ev'], 3)} \\\\",
            f"curated path table {row['family']} {row['path_id']}",
        )
        n_checks += 1

    md_rows = read_csv(curated_root / "results/production_md_runs.csv")
    assert_true(len(md_rows) == 18, "curated production MD row count is not 18")
    assert_true(all(row["completed_target"] == "True" for row in md_rows), "curated production MD is incomplete")
    assert_true(all(row["lost_atoms_or_error"] == "False" for row in md_rows), "curated production MD has lost atoms or errors")
    assert_true(all(row["dangerous_builds"] == "0" for row in md_rows), "curated production MD has dangerous builds")
    contains(text, "18/18 target-length trajectories", "curated production MD completion")
    n_checks += 5

    def md_group(family: str, model_family: str) -> list[dict[str, str]]:
        rows = [
            row
            for row in md_rows
            if row["structure"] == family and row["model_family"] == model_family
        ]
        assert_true(len(rows) == 3, f"curated MD group is not three rows: {family}/{model_family}")
        return rows

    all_msd = [float(row["final_msd_xy_a2"]) for row in md_rows]
    contains(text, f"span {fmt(min(all_msd), 1)}--{fmt(max(all_msd), 1)} \\AA$^2$", "curated MD range")
    n_checks += 1
    md_specs = [
        ("A_Perfect", "finetuned_reference", "Pristine graphene & Reference model", "500"),
        ("B1_Monovacancy", "committee_model", "Monovacancy graphene & Committee models", "200"),
        ("B2_Divacancy", "committee_model", "Divacancy graphene & Committee models", "200"),
        ("C_StoneWales", "finetuned_reference", "Stone--Wales graphene & Reference model", "500"),
        ("D_SiGraphene", "committee_model", "Si$_4$--graphene motif & Committee models", "200"),
        ("D_SiGraphene", "finetuned_reference", "Si$_4$--graphene motif & Reference model", "500"),
    ]
    md_ranges: dict[tuple[str, str], tuple[float, float]] = {}
    for family, model_family, label, ps in md_specs:
        values = [float(row["final_msd_xy_a2"]) for row in md_group(family, model_family)]
        low, high = min(values), max(values)
        md_ranges[(family, model_family)] = (low, high)
        contains(
            text,
            f"{label} & {ps} & 3/3 & Stable completion; final MSD$_{{xy}}$ = "
            f"{fmt(low, 1)}--{fmt(high, 1)} \\AA$^2$ \\\\",
            f"curated MD table {family}/{model_family}",
        )
        n_checks += 1
    d_ref_low, d_ref_high = md_ranges[("D_SiGraphene", "finetuned_reference")]
    d_com_low, d_com_high = md_ranges[("D_SiGraphene", "committee_model")]
    for snippet, label in (
        (
            f"they span {fmt(d_ref_low, 1)}--{fmt(d_ref_high, 1)} \\AA$^2$ in the three 500 ps reference-model runs",
            "curated Si4 reference MD range",
        ),
        (
            f"and {fmt(d_com_low, 1)}--{fmt(d_com_high, 1)} \\AA$^2$ in the three 200 ps committee-model runs",
            "curated Si4 committee MD range",
        ),
        (f"differ by {fmt(d_ref_high - d_ref_low, 1)} \\AA$^2$", "curated Si4 reference MD spread"),
        (f"differ by {fmt(d_com_high - d_com_low, 1)} \\AA$^2$", "curated Si4 committee MD spread"),
    ):
        contains(text, snippet, label)
        n_checks += 1

    dft_rows = read_csv(curated_root / "results/initial_snapshot_dft_evidence.csv")
    assert_true(len(dft_rows) == 9, "curated snapshot DFT row count is not 9")
    assert_true(all(row["completed"] == "True" for row in dft_rows), "curated snapshot DFT is incomplete")
    assert_true(
        all(row["electronic_converged_marker"] == "True" for row in dft_rows),
        "curated snapshot DFT is not electronically converged",
    )
    assert_true(all(row["fatal_error"] == "False" for row in dft_rows), "curated snapshot DFT has a fatal marker")
    assert_true(all(row["forces_readable"] == "True" for row in dft_rows), "curated snapshot DFT forces are unreadable")
    n_checks += 5
    for row in dft_rows:
        case_label = "Si$_4$--graphene" if row["case"] == "D_SiGraphene" else "Monovacancy graphene"
        contains(
            text,
            f"{case_label} & {row['seed']}/{int(row['step'])} & {fmt(row['time_ps'], 1)} "
            f"& {fmt(row['msd_xy_a2'], 1)} & {fmt(row['dft_energy_without_entropy_ev'], 3)} &",
            f"curated snapshot DFT table {row['case']} {row['seed']}/{row['step']}",
        )
        n_checks += 1

    foundation_summary = {
        row["group"]: row
        for row in read_csv(curated_root / "results/foundation_snapshot_force_summary.csv")
    }
    grouped_summary = {
        row["group"]: row
        for row in read_csv(curated_root / "results/grouped_e0_snapshot_force_summary.csv")
    }

    def summary_force(rows: dict[str, dict[str, str]], group: str) -> float:
        assert_true(group in rows, f"missing curated snapshot-force group: {group}")
        return float(rows[group]["force_rmse_mev_a_frame_rms"])

    force_claims = (
        (foundation_summary, "ALL", "force RMSE of {value} meV \\AA$^{{-1}}$", "curated foundation all force"),
        (foundation_summary, "B1_Monovacancy", "including {value} meV \\AA$^{{-1}}$", "curated foundation B1 force"),
        (foundation_summary, "D_SiGraphene", "and {value} meV \\AA$^{{-1}}$", "curated foundation Si4 force"),
        (grouped_summary, "D_SiGraphene", "to {value} meV \\AA$^{{-1}}$", "curated grouped-E0 Si4 force"),
        (grouped_summary, "B1_Monovacancy", "remains {value} meV \\AA$^{{-1}}$", "curated grouped-E0 B1 force"),
        (grouped_summary, "ALL", "remains {value} meV \\AA$^{{-1}}$", "curated grouped-E0 all force"),
    )
    for rows, group, template, label in force_claims:
        value = fmt(summary_force(rows, group), 0)
        contains(text, template.format(value=value), label)
        n_checks += 1

    foundation_errors = read_csv(curated_root / "results/foundation_snapshot_force_errors.csv")
    b1_cc = sorted(
        float(row["min_C_C_a"])
        for row in foundation_errors
        if row["case"] == "B1_Monovacancy" and row["min_C_C_a"] != "nan"
    )
    si_si = sorted(
        float(row["min_Si_Si_a"])
        for row in foundation_errors
        if row["case"] == "D_SiGraphene" and row["min_Si_Si_a"] != "nan"
    )
    assert_true(len(b1_cc) == 3, "curated monovacancy contact count is not 3")
    assert_true(si_si, "curated Si4 contact list is empty")
    contains(
        text,
        f"minimum C--C contacts of {fmt(b1_cc[0], 3)}, {fmt(b1_cc[1], 3)}, and {fmt(b1_cc[2], 3)} \\AA{{}}",
        "curated monovacancy contacts",
    )
    contains(text, f"minimum Si--Si contact of {fmt(si_si[0], 3)} \\AA{{}}", "curated Si4 contact")
    n_checks += 4

    readme = read_text(curated_root / "README.md")
    for snippet in (
        "VASP 5.4.1",
        "C (08Apr2002), Li_sv (10Sep2004), and Si",
        "MACE 0.3.15",
        "MACE 0.3.16",
        "RTX 5080",
        "PyTorch 2.11.0+cu128",
        "CUDA 12.8",
        "LAMMPS 10 September 2025",
        "a = 2.46 A",
        "30.0 A",
        "C50LiSi4",
        "non-substitutional Si atoms",
        "deterministic 8:1:1",
        "Becke-Johnson damping (IVDW = 12)",
        "LDIPOL = True, IDIPOL = 3",
    ):
        assert_true(snippet in readme, f"curated README provenance changed: {snippet}")
        n_checks += 1
    for snippet, label in (
        ("VASP 5.4.1", "curated manuscript VASP version"),
        ("PAW\\_PBE datasets as C (08Apr2002), Li\\_sv (10Sep2004), and Si (05Jan2001)", "curated manuscript PAW labels"),
        ("MACE 0.3.16", "curated manuscript MACE version"),
        ("LAMMPS (10 September 2025)", "curated manuscript LAMMPS version"),
        (r"A graphene lattice parameter of 2.46 \AA{} and a 5 $\times$ 5 supercell", "curated manuscript initial cell"),
        (r"The 30.0 \AA{} cell height places 15.0 \AA{} of vacuum on each side", "curated manuscript slab vacuum"),
        (r"four non-substitutional Si atoms above the intact C$_{50}$ sheet", "curated manuscript Si4 construction"),
        ("DFT-D3 method with Becke--Johnson damping (PBE-D3(BJ); IVDW = 12)", "curated manuscript D3(BJ) method"),
        ("slab dipole correction (LDIPOL = .TRUE., IDIPOL = 3)", "curated manuscript adsorption dipole"),
    ):
        contains(text, snippet, label)
        n_checks += 1
    return n_checks


def main() -> int:
    global CURATED_ROOT, EVIDENCE_ROOT

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
    parser.add_argument(
        "--curated-only",
        action="store_true",
        help="Verify only the redistributable submission_data package and manuscript.",
    )
    parser.add_argument(
        "--curated-root",
        type=Path,
        default=CURATED_ROOT,
        help="Root of the redistributable curated evidence package.",
    )
    args = parser.parse_args()

    EVIDENCE_ROOT = args.evidence_root.resolve()
    CURATED_ROOT = args.curated_root.resolve()

    try:
        text = read_text(args.tex)
        if args.curated_only:
            checks = check_curated_submission(text, CURATED_ROOT)
        else:
            checks = 0
            checks += check_author_and_dataset(text)
            checks += check_mace_errors(text)
            checks += check_adsorption_and_paths(text)
            checks += check_md_and_snapshots(text)
            checks += check_scheduler_gates_and_language(text)
            checks += check_method_provenance(text)
    except AssertionError as exc:
        mode = "curated manuscript verification" if args.curated_only else "manuscript numeric verification"
        print(f"FAILED {mode}: {exc}", file=sys.stderr)
        return 1

    mode = "curated manuscript verification" if args.curated_only else "manuscript numeric verification"
    print(f"PASSED {mode}: checks={checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
