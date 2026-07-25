#!/usr/bin/env bash
#SBATCH -J li-rush-analysis
#SBATCH -p et2_medmem,et3_medmem,et4_medmem,et2,et3,et4,et1_new
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=08:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
cd "${PROJECT_ROOT}"
mkdir -p logs results/two_day_rush

if ! type module >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
fi

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
fi

# shellcheck disable=SC1091
source /home/xh121/anaconda3/etc/profile.d/conda.sh
conda activate mace_md

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"

echo "Running rapid two-day analysis on $(hostname)"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unknown}"
python check_sp_jobs.py --jobs-root dft_sp_outputs --report results/two_day_rush/sp_job_status.json
python rapid_results_analysis.py \
    --dataset-dir data/mace_datasets \
    --sp-root dft_sp_outputs \
    --output-dir results/two_day_rush \
    --device cpu \
    --dtype float32 \
    --max-parity-frames 500

echo "Rapid analysis complete: results/two_day_rush/SUMMARY.md"
