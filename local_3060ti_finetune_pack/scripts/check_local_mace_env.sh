#!/usr/bin/env bash
# Check that the existing local 3060 Ti conda environment can run MACE training.
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

nvidia-smi || true

python - <<'PY'
from ase.io import read
from pathlib import Path
import numpy as np
import shutil
import subprocess
import sys
import torch

print("python", sys.version.split()[0])
print("torch", torch.__version__)
print("torch_cuda", torch.version.cuda)
print("cuda_available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
print("mace_run_train", shutil.which("mace_run_train"))
if shutil.which("mace_run_train") is None:
    raise SystemExit("mace_run_train is not on PATH")

required = ["--foundation_model", "--valid_file", "--test_file", "--lr_params_factors"]
help_text = subprocess.check_output(["mace_run_train", "--help"], text=True)
missing = [flag for flag in required if flag not in help_text]
if missing:
    raise SystemExit(f"mace_run_train is missing flags: {missing}")

for split in ["train", "valid", "test"]:
    path = Path(f"data/mace_datasets/li_mace_{split}.extxyz")
    frames = read(path, ":")
    if not isinstance(frames, list):
        frames = [frames]
    max_force = max(float(np.abs(frame.get_forces()).max()) for frame in frames)
    print(split, len(frames), "frames", "max_force", f"{max_force:.3f}")

print("Environment and dataset check passed.")
PY
