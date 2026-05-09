#!/usr/bin/env bash
# Step 3: create fixed-geometry VASP single-point job directories.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
CONDA_BASE="${CONDA_BASE:-/home/xh121/anaconda3}"
ENV_NAME="${ENV_NAME:-mace_md}"
POTCAR_ROOT="${POTCAR_ROOT:-${PROJECT_ROOT}/potentials/potpaw_PBE_54}"

cd "${PROJECT_ROOT}"

if [[ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]]; then
    # shellcheck disable=SC1091
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    conda activate "${ENV_NAME}"
fi

python prepare_vasp_jobs.py \
    --structures-dir structures/li_sampling \
    --output-dir dft_sp_outputs \
    --mode singlepoint \
    --potcar-root "${POTCAR_ROOT}" \
    --ntasks "${NTASKS:-16}" \
    --mem "${MEM:-16G}" \
    --time "${TIME_LIMIT:-04:00:00}"
