#!/usr/bin/env bash
# Five-epoch local fine-tune check before the full run.
set -euo pipefail

export MODEL_NAME="${MODEL_NAME:-li_mace_v1_3060ti_smoke}"
export MODEL_DIR="${MODEL_DIR:-models/local_finetuned_li_mace_v1_smoke}"
export RESULTS_DIR="${RESULTS_DIR:-results/local_li_mace_v1_smoke}"
export CHECKPOINTS_DIR="${CHECKPOINTS_DIR:-checkpoints/local_li_mace_v1_smoke}"
export LOGS_DIR="${LOGS_DIR:-logs/local_li_mace_v1_smoke}"
export MAX_NUM_EPOCHS="${MAX_NUM_EPOCHS:-5}"
export START_SWA="${START_SWA:-4}"
export BATCH_SIZE="${BATCH_SIZE:-1}"
export VALID_BATCH_SIZE="${VALID_BATCH_SIZE:-1}"
export CONVERT_FOR_LAMMPS="${CONVERT_FOR_LAMMPS:-0}"

bash "$(dirname "${BASH_SOURCE[0]}")/run_local_finetune_3060ti.sh"
