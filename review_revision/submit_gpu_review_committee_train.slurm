#!/usr/bin/env bash
# Train a small seed committee for model-uncertainty diagnostics.
#
# Submit:
#   sbatch review_revision/submit_gpu_review_committee_train.slurm

#SBATCH -J li-review-committee
#SBATCH -p et_gpu
#SBATCH --array=0-2
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
SEEDS=(20260427 20260428 20260429)
SEED="${SEEDS[$SLURM_ARRAY_TASK_ID]}"

cd "${PROJECT_ROOT}"
mkdir -p logs results/review_revision checkpoints/review_revision models/review_revision

export TRAIN_FILE="${PROJECT_ROOT}/data/mace_datasets/li_mace_train.extxyz"
export VALID_FILE="${PROJECT_ROOT}/data/mace_datasets/li_mace_valid.extxyz"
export TEST_FILE="${PROJECT_ROOT}/data/mace_datasets/li_mace_test.extxyz"
export FOUNDATION_MODEL="${PROJECT_ROOT}/models/foundation/mace-mpa-0-medium.model"
export MODEL_NAME="li_mace_review_seed${SEED}"
export MODEL_DIR="${PROJECT_ROOT}/models/review_revision"
export RESULTS_DIR="${PROJECT_ROOT}/results/review_revision/${MODEL_NAME}"
export CHECKPOINTS_DIR="${PROJECT_ROOT}/checkpoints/review_revision/${MODEL_NAME}"
export LOGS_DIR="${PROJECT_ROOT}/logs/review_revision/${MODEL_NAME}"
export BATCH_SIZE="${BATCH_SIZE:-4}"
export VALID_BATCH_SIZE="${VALID_BATCH_SIZE:-4}"
export MAX_NUM_EPOCHS="${MAX_NUM_EPOCHS:-300}"
export START_SWA="${START_SWA:-225}"
export LR="${LR:-0.001}"
export DEVICE="${DEVICE:-cuda}"
export DEFAULT_DTYPE="${DEFAULT_DTYPE:-float64}"
export SEED
export CONVERT_FOR_LAMMPS="${CONVERT_FOR_LAMMPS:-0}"

bash run_finetune.sh
