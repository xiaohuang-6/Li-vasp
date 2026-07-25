#!/usr/bin/env bash
# Reviewer task 1: compare fine-tuned and foundation MACE on train/valid/test splits.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-mace_review_5080}"
DTYPE="${MACE_DTYPE:-float32}"

CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

cd "${ROOT}"
mkdir -p results/review_revision/mace_eval logs

python review_revision/evaluate_mace_on_splits.py \
    --model models/finetuned_reference/li_mace_v1_3060ti.model --model-label finetuned_3060ti \
    --model models/foundation/mace-mpa-0-medium.model --model-label foundation_mpa0 \
    --output-dir results/review_revision/mace_eval \
    --device cuda \
    --dtype "${DTYPE}" | tee logs/run_01_mace_eval.log
