#!/usr/bin/env bash
# Step 2: generate Li adsorption/path POSCAR files for new SP labels.
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

python generate_li_sampling_structures.py \
    --input-root dft_outputs \
    --output-dir structures/li_sampling \
    --path-images "${PATH_IMAGES:-5}" \
    --summary structures/li_sampling/li_sampling_summary.json
