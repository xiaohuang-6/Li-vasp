#!/usr/bin/env bash
# Step 4: build train/valid/test extxyz files after SP OUTCARs finish.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
CONDA_BASE="${CONDA_BASE:-/home/xh121/anaconda3}"
ENV_NAME="${ENV_NAME:-mace_md}"

cd "${PROJECT_ROOT}"

if [[ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]]; then
    # shellcheck disable=SC1091
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    conda activate "${ENV_NAME}"
fi

python check_sp_jobs.py --jobs-root dft_sp_outputs --report dft_sp_outputs/sp_job_status.json

python build_mace_datasets.py \
    --extxyz data/relax_all_frames.extxyz \
    --outcar-glob "dft_sp_outputs/**/OUTCAR" \
    --output-dir data/mace_datasets \
    --prefix li_mace
