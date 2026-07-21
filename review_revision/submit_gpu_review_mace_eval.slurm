#!/usr/bin/env bash
# Evaluate foundation and fine-tuned MACE models on train/valid/test splits.

#SBATCH -J li-review-mace-eval
#SBATCH -p et_gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
FOUNDATION_MODEL="${FOUNDATION_MODEL:-${PROJECT_ROOT}/models/foundation/mace-mpa-0-medium.model}"
FINETUNED_MODEL="${FINETUNED_MODEL:-${PROJECT_ROOT}/local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1/li_mace_v1_3060ti_stagetwo.model}"

cd "${PROJECT_ROOT}"
mkdir -p logs results/review_revision/mace_eval

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
    module load cuda >/dev/null 2>&1 || true
fi

source /home/xh121/anaconda3/etc/profile.d/conda.sh
conda activate mace_md

python review_revision/evaluate_mace_on_splits.py \
    --model "${FINETUNED_MODEL}" --model-label finetuned \
    --model "${FOUNDATION_MODEL}" --model-label foundation \
    --output-dir results/review_revision/mace_eval \
    --device cuda \
    --dtype float64
