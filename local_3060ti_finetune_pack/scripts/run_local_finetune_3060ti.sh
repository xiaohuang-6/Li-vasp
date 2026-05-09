#!/usr/bin/env bash
# Fine-tune MACE locally on an RTX 3060 Ti using the fixed train/valid/test split.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-mace_md_local}"

cd "${ROOT}"

if command -v conda >/dev/null 2>&1; then
    CONDA_BASE="$(conda info --base)"
else
    CONDA_BASE="${CONDA_BASE:-${HOME}/miniforge3}"
fi

if [[ ! -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]]; then
    echo "Cannot find conda.sh under ${CONDA_BASE}" >&2
    echo "Set CONDA_BASE=/path/to/miniforge3 or create the local MACE env first." >&2
    exit 1
fi

# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

python - <<'PY'
import sys
import torch
if not torch.cuda.is_available():
    print("torch.cuda.is_available() is false. Use DEVICE=cpu only for debugging.", file=sys.stderr)
    sys.exit(1)
print("Using GPU:", torch.cuda.get_device_name(0))
PY

export CONDA_BASE
export ENV_NAME
export PROJECT_ROOT="${ROOT}"
export TRAIN_FILE="${TRAIN_FILE:-data/mace_datasets/li_mace_train.extxyz}"
export VALID_FILE="${VALID_FILE:-data/mace_datasets/li_mace_valid.extxyz}"
export TEST_FILE="${TEST_FILE:-data/mace_datasets/li_mace_test.extxyz}"
export FOUNDATION_MODEL="${FOUNDATION_MODEL:-models/foundation/mace-mpa-0-medium.model}"
export MODEL_NAME="${MODEL_NAME:-li_mace_v1_3060ti}"
export MODEL_DIR="${MODEL_DIR:-models/local_finetuned_li_mace_v1}"
export RESULTS_DIR="${RESULTS_DIR:-results/local_li_mace_v1}"
export CHECKPOINTS_DIR="${CHECKPOINTS_DIR:-checkpoints/local_li_mace_v1}"
export LOGS_DIR="${LOGS_DIR:-logs/local_li_mace_v1}"

# RTX 3060 Ti has limited FP64 throughput and usually 8 GB VRAM.
export DEVICE="${DEVICE:-cuda}"
export DEFAULT_DTYPE="${DEFAULT_DTYPE:-float32}"
export BATCH_SIZE="${BATCH_SIZE:-2}"
export VALID_BATCH_SIZE="${VALID_BATCH_SIZE:-2}"
export MAX_NUM_EPOCHS="${MAX_NUM_EPOCHS:-300}"
export START_SWA="${START_SWA:-225}"
export LR="${LR:-0.0005}"
export ENERGY_KEY="${ENERGY_KEY:-energy}"
export FORCES_KEY="${FORCES_KEY:-forces}"
export CONVERT_FOR_LAMMPS="${CONVERT_FOR_LAMMPS:-1}"

mkdir -p logs
timestamp="$(date +%Y%m%d_%H%M%S)"
log_file="logs/local_finetune_${timestamp}.log"

echo "Writing combined log to ${log_file}"
bash run_finetune.sh 2>&1 | tee "${log_file}"
