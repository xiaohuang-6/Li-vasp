#!/usr/bin/env bash
# Evaluate fine-tuned and foundation MACE models on train/valid/test splits.
#
# Submit:
#   sbatch review_revision/submit_gpu_review_mace_eval.slurm

#SBATCH -J li-review-eval
#SBATCH -p et_gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
CONDA_BASE="${CONDA_BASE:-/home/xh121/anaconda3}"
ENV_NAME="${ENV_NAME:-mace_md}"
FOUNDATION_MODEL="${FOUNDATION_MODEL:-${PROJECT_ROOT}/models/foundation/mace-mpa-0-medium.model}"
FINETUNED_MODEL="${FINETUNED_MODEL:-${PROJECT_ROOT}/local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model}"
OUTDIR="${OUTDIR:-${PROJECT_ROOT}/results/review_revision/mace_eval}"

cd "${PROJECT_ROOT}"
mkdir -p logs "${OUTDIR}"
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

python review_revision/evaluate_mace_on_splits.py \
    --model "${FINETUNED_MODEL}" --model-label finetuned \
    --model "${FOUNDATION_MODEL}" --model-label foundation \
    --output-dir "${OUTDIR}" \
    --device cuda \
    --dtype float64
