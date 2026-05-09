#!/usr/bin/env bash
#SBATCH -J li-mace-train
#SBATCH -p et_gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --mem=64G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
CONDA_BASE="${CONDA_BASE:-/home/xh121/anaconda3}"
ENV_NAME="${ENV_NAME:-mace_md}"

mkdir -p "${PROJECT_ROOT}/logs"
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"
cd "${PROJECT_ROOT}"

if [[ ! -s models/foundation/mace-mpa-0-medium.model ]]; then
    python download_mace.py --destination models/foundation
fi

export TRAIN_FILE="${TRAIN_FILE:-data/mace_datasets/li_mace_train.extxyz}"
export VALID_FILE="${VALID_FILE:-data/mace_datasets/li_mace_valid.extxyz}"
export TEST_FILE="${TEST_FILE:-data/mace_datasets/li_mace_test.extxyz}"
export FOUNDATION_MODEL="${FOUNDATION_MODEL:-models/foundation/mace-mpa-0-medium.model}"
export MODEL_NAME="${MODEL_NAME:-li_mace_v1}"
export MODEL_DIR="${MODEL_DIR:-models/finetuned_li_mace_v1}"
export RESULTS_DIR="${RESULTS_DIR:-results/li_mace_v1}"
export CHECKPOINTS_DIR="${CHECKPOINTS_DIR:-checkpoints/li_mace_v1}"
export LOGS_DIR="${LOGS_DIR:-logs/li_mace_v1}"
export BATCH_SIZE="${BATCH_SIZE:-4}"
export VALID_BATCH_SIZE="${VALID_BATCH_SIZE:-4}"
export MAX_NUM_EPOCHS="${MAX_NUM_EPOCHS:-300}"
export START_SWA="${START_SWA:-225}"
export LR="${LR:-0.001}"
export DEVICE="${DEVICE:-cuda}"
export DEFAULT_DTYPE="${DEFAULT_DTYPE:-float64}"
export ENERGY_KEY="${ENERGY_KEY:-energy}"
export FORCES_KEY="${FORCES_KEY:-forces}"
export CONVERT_FOR_LAMMPS="${CONVERT_FOR_LAMMPS:-1}"

bash run_finetune.sh
