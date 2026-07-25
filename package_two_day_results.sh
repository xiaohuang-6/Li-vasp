#!/usr/bin/env bash
# Rebuild the two-day rush deliverable archive from the current workspace state.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
cd "${PROJECT_ROOT}"

ARCHIVE="results/two_day_rush_deliverable_20260708.tar.gz"
mkdir -p results

tar -czf "${ARCHIVE}" \
  README_TWO_DAY_RUSH.md \
  results/two_day_rush \
  manuscript make_structure_figure.py make_review_revised_figures.py review_revision \
  data/lammps \
  lammps_logs/two_day_md \
  trajectories/two_day_md \
  local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1 \
  rapid_results_analysis.py analyze_short_md.py write_paper_results_brief.py \
  write_manuscript_results_draft.py write_md_quality_notes.py make_results_manifest.py \
  refresh_current_stable_md.py package_two_day_results.sh \
  scripts_prepare_two_day_lammps_data.sh scripts_cpu_scaling_benchmark.sh \
  submit_cpu_rapid_analysis.slurm submit_cpu_short_md_array.slurm \
  submit_cpu_md_fast_postprocess.slurm submit_cpu_md_800k_postprocess.slurm \
  submit_cpu_md_400k_stable_postprocess.slurm submit_cpu_md_400k_stable2p5_postprocess.slurm \
  submit_cpu_md_400k_stable_window_postprocess.slurm submit_cpu_md_postprocess.slurm \
  submit_cpu_lammps_scaling.slurm submit_cpu_lammps_scaling_flexible.slurm \
  in.lammps_short_cpu in.lammps_scaling_cpu

ls -lh "${ARCHIVE}"
