#!/usr/bin/env bash
# Step 1: extract all ionic relaxation frames from existing converged OUTCARs.
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

python vasp_to_extxyz.py \
    --input-glob "dft_outputs/**/OUTCAR" \
    --output data/relax_all_frames.extxyz \
    --all-steps \
    --report data/relax_all_frames.report.json

python - <<'PY'
from ase.io import read
frames = read("data/relax_all_frames.extxyz", ":")
print(f"relax_all_frames: {len(frames)} frames")
for atoms in frames[:5]:
    print(atoms.info.get("config_type"), len(atoms), atoms.get_potential_energy(), atoms.get_forces().shape)
PY
