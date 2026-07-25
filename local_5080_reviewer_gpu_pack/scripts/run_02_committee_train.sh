#!/usr/bin/env bash
# Reviewer task 2: train a small fine-tuned MACE committee for uncertainty diagnostics.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-mace_review_5080}"
SEED_LIST="${SEED_LIST:-20260427 20260428 20260429}"

CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"
export CONDA_BASE ENV_NAME

cd "${ROOT}"
mkdir -p logs results/review_revision checkpoints/review_revision models/review_revision

for seed in ${SEED_LIST}; do
    export TRAIN_FILE="${ROOT}/data/mace_datasets/li_mace_train.extxyz"
    export VALID_FILE="${ROOT}/data/mace_datasets/li_mace_valid.extxyz"
    export TEST_FILE="${ROOT}/data/mace_datasets/li_mace_test.extxyz"
    export FOUNDATION_MODEL="${ROOT}/models/foundation/mace-mpa-0-medium.model"
    export MODEL_NAME="li_mace_review_seed${seed}"
    export MODEL_DIR="${ROOT}/models/review_revision"
    export RESULTS_DIR="${ROOT}/results/review_revision/${MODEL_NAME}"
    export CHECKPOINTS_DIR="${ROOT}/checkpoints/review_revision/${MODEL_NAME}"
    export LOGS_DIR="${ROOT}/logs/review_revision/${MODEL_NAME}"
    export BATCH_SIZE="${BATCH_SIZE:-4}"
    export VALID_BATCH_SIZE="${VALID_BATCH_SIZE:-4}"
    export MAX_NUM_EPOCHS="${MAX_NUM_EPOCHS:-300}"
    export START_SWA="${START_SWA:-225}"
    export LR="${LR:-0.001}"
    export DEVICE="${DEVICE:-cuda}"
    export DEFAULT_DTYPE="${DEFAULT_DTYPE:-float32}"
    export SEED="${seed}"
    export CONVERT_FOR_LAMMPS="${CONVERT_FOR_LAMMPS:-0}"
    echo "Training committee seed ${seed}"
    bash run_finetune.sh 2>&1 | tee "logs/review_committee_seed${seed}.log"
done
