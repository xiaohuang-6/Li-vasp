#!/usr/bin/env bash
# Collect converged DFT evidence, then run MACE inference explicitly on the CPU.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
CONDA="${CONDA:-conda}"
ENV_NAME="${ENV_NAME:-mace_md}"
FOUNDATION_MODEL="${FOUNDATION_MODEL:-${PROJECT_ROOT}/models/foundation/mace-mpa-0-medium.model}"
GROUPED_E0_MODEL="${GROUPED_E0_MODEL:-${PROJECT_ROOT}/submission_data/models/li_mace_grouped_e0_seed20260430.model}"
D3_MANIFEST="${D3_MANIFEST:-${PROJECT_ROOT}/review_revision/d3_site_converged_jobs/manifest.csv}"
SNAPSHOT_MANIFEST="${SNAPSHOT_MANIFEST:-${PROJECT_ROOT}/review_revision/high_displacement_converged_jobs/combined_manifest.csv}"

cd "${PROJECT_ROOT}"
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

"${CONDA}" run --no-capture-output -n "${ENV_NAME}" \
    python review_revision/collect_balanced_perturbation_dft.py

"${CONDA}" run --no-capture-output -n "${ENV_NAME}" \
    python review_revision/collect_d3_site_robustness.py \
    --manifest "${D3_MANIFEST}"

"${CONDA}" run --no-capture-output -n "${ENV_NAME}" \
    python review_revision/evaluate_balanced_perturbation_forces.py \
    --device cpu \
    --model "${FOUNDATION_MODEL}" \
    --model-label foundation_mpa0 \
    --model "${GROUPED_E0_MODEL}" \
    --model-label grouped_e0

"${CONDA}" run --no-capture-output -n "${ENV_NAME}" \
    python review_revision/archive_md_snapshot_evidence.py \
    --manifest "${SNAPSHOT_MANIFEST}" \
    --output-prefix review_revision/SNAPSHOT_DFT_EVIDENCE

"${CONDA}" run --no-capture-output -n "${ENV_NAME}" \
    python review_revision/evaluate_mace_snapshot_forces.py \
    --manifest "${SNAPSHOT_MANIFEST}" \
    --device cpu \
    --model "${FOUNDATION_MODEL}" \
    --model-label foundation_mpa0 \
    --model "${GROUPED_E0_MODEL}" \
    --model-label grouped_e0 \
    --output-dir results/review_revision/high_displacement_mace_eval_strict

echo "CPU-only science-strengthening postprocessing complete."
