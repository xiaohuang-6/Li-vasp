#!/usr/bin/env bash
# Fine-tune a MACE foundation model on the extxyz data and create a LAMMPS model.
set -euo pipefail

export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
CONDA_BASE="${CONDA_BASE:-/home/xh121/anaconda3}"
ENV_NAME="${ENV_NAME:-mace_md}"

TRAIN_FILE="${TRAIN_FILE:-data/train_data.extxyz}"
VALID_FILE="${VALID_FILE:-}"
TEST_FILE="${TEST_FILE:-}"
FOUNDATION_MODEL="${FOUNDATION_MODEL:-models/foundation/mace-mpa-0-medium.model}"
MODEL_NAME="${MODEL_NAME:-li_graphene_mace}"
MODEL_DIR="${MODEL_DIR:-models/finetuned}"
RESULTS_DIR="${RESULTS_DIR:-results}"
CHECKPOINTS_DIR="${CHECKPOINTS_DIR:-checkpoints}"
LOGS_DIR="${LOGS_DIR:-logs}"

BATCH_SIZE="${BATCH_SIZE:-2}"
VALID_BATCH_SIZE="${VALID_BATCH_SIZE:-2}"
VALID_FRACTION="${VALID_FRACTION:-0.10}"
MAX_NUM_EPOCHS="${MAX_NUM_EPOCHS:-300}"
START_SWA="${START_SWA:-225}"
LR="${LR:-0.001}"
DEVICE="${DEVICE:-cuda}"
DEFAULT_DTYPE="${DEFAULT_DTYPE:-float64}"
SEED="${SEED:-20260427}"
CONVERT_FOR_LAMMPS="${CONVERT_FOR_LAMMPS:-1}"
ENERGY_KEY="${ENERGY_KEY:-energy}"
FORCES_KEY="${FORCES_KEY:-forces}"

LR_PARAMS_FACTORS="${LR_PARAMS_FACTORS:-{\"embedding_lr_factor\":0.0,\"interactions_lr_factor\":0.0,\"products_lr_factor\":1.0,\"readouts_lr_factor\":1.0}}"

if [[ ! -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]]; then
    echo "Cannot find conda.sh under ${CONDA_BASE}" >&2
    exit 1
fi

source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

cd "${PROJECT_ROOT}"
mkdir -p "${MODEL_DIR}" "${RESULTS_DIR}" "${CHECKPOINTS_DIR}" "${LOGS_DIR}"

if [[ ! -s "${TRAIN_FILE}" ]]; then
    echo "Training file not found or empty: ${TRAIN_FILE}" >&2
    echo "Run vasp_to_extxyz.py after placing OUTCAR files under dft_outputs/." >&2
    exit 1
fi

if [[ -n "${VALID_FILE}" && ! -s "${VALID_FILE}" ]]; then
    echo "Validation file was requested but is missing or empty: ${VALID_FILE}" >&2
    exit 1
fi

if [[ -n "${TEST_FILE}" && ! -s "${TEST_FILE}" ]]; then
    echo "Test file was requested but is missing or empty: ${TEST_FILE}" >&2
    exit 1
fi

if [[ ! -s "${FOUNDATION_MODEL}" ]]; then
    echo "Foundation model not found: ${FOUNDATION_MODEL}" >&2
    echo "Run python download_mace.py or place the model at this path." >&2
    exit 1
fi

python inspect_mace_model.py "${FOUNDATION_MODEL}" \
    --check-train-cli \
    --json-output "${LOGS_DIR}/${MODEL_NAME}_foundation_inspection.json"

echo "MACE fine-tuning inputs:"
echo "  train: ${TRAIN_FILE}"
if [[ -n "${VALID_FILE}" ]]; then
    echo "  valid: ${VALID_FILE}"
else
    echo "  valid_fraction: ${VALID_FRACTION}"
fi
if [[ -n "${TEST_FILE}" ]]; then
    echo "  test: ${TEST_FILE}"
fi
echo "  model_name: ${MODEL_NAME}"
echo "  device: ${DEVICE}"
echo "  dtype: ${DEFAULT_DTYPE}"

TRAIN_CMD=(
    mace_run_train
    "--name=${MODEL_NAME}"
    "--foundation_model=${FOUNDATION_MODEL}"
    "--multiheads_finetuning=False"
    "--train_file=${TRAIN_FILE}"
    "--energy_weight=1.0"
    "--forces_weight=100.0"
    "--energy_key=${ENERGY_KEY}"
    "--forces_key=${FORCES_KEY}"
    "--loss=universal"
    "--E0s=average"
    "--lr=${LR}"
    "--lr_params_factors=${LR_PARAMS_FACTORS}"
    "--scaling=rms_forces_scaling"
    "--batch_size=${BATCH_SIZE}"
    "--valid_batch_size=${VALID_BATCH_SIZE}"
    "--max_num_epochs=${MAX_NUM_EPOCHS}"
    "--swa"
    "--start_swa=${START_SWA}"
    "--ema"
    "--ema_decay=0.99"
    "--amsgrad"
    "--restart_latest"
    "--default_dtype=${DEFAULT_DTYPE}"
    "--device=${DEVICE}"
    "--seed=${SEED}"
    "--model_dir=${MODEL_DIR}"
    "--results_dir=${RESULTS_DIR}"
    "--checkpoints_dir=${CHECKPOINTS_DIR}"
    "--log_dir=${LOGS_DIR}"
)

if [[ -n "${VALID_FILE}" ]]; then
    TRAIN_CMD+=("--valid_file=${VALID_FILE}")
else
    TRAIN_CMD+=("--valid_fraction=${VALID_FRACTION}")
fi

if [[ -n "${TEST_FILE}" ]]; then
    TRAIN_CMD+=("--test_file=${TEST_FILE}")
fi

"${TRAIN_CMD[@]}"

TRAINED_MODEL="${MODEL_DIR}/${MODEL_NAME}.model"
if [[ ! -s "${TRAINED_MODEL}" ]]; then
    TRAINED_MODEL="$(find "${MODEL_DIR}" -maxdepth 1 -name "${MODEL_NAME}*.model" -printf '%T@ %p\n' | sort -nr | awk 'NR==1 {print $2}')"
fi

if [[ -z "${TRAINED_MODEL}" || ! -s "${TRAINED_MODEL}" ]]; then
    echo "Could not locate trained model under ${MODEL_DIR}" >&2
    exit 1
fi

echo "Trained model: ${TRAINED_MODEL}"

if [[ "${CONVERT_FOR_LAMMPS}" == "1" ]]; then
    python convert_model_for_lammps.py "${TRAINED_MODEL}" --format=libtorch --dtype="${DEFAULT_DTYPE}"
fi
