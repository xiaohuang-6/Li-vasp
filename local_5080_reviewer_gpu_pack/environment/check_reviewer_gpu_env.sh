#!/usr/bin/env bash
# Validate local RTX 5080 reviewer GPU environment and required input files.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-mace_review_5080}"

if ! command -v conda >/dev/null 2>&1; then
    echo "conda not found. Run environment/setup_mace_env_5080.sh after installing Miniforge/Miniconda." >&2
    exit 1
fi

CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

cd "${ROOT}"

nvidia-smi || {
    echo "nvidia-smi failed. Install a recent NVIDIA driver before running RTX 5080 jobs." >&2
    exit 1
}

python - <<'PY'
from pathlib import Path
import shutil
import torch

print("torch:", torch.__version__, "cuda:", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit("torch.cuda.is_available() is false")
print("gpu:", torch.cuda.get_device_name(0))
print("capability:", torch.cuda.get_device_capability(0))
if torch.cuda.get_device_capability(0) < (12, 0):
    print("WARNING: GPU is not Blackwell-class; scripts may still run, but this pack is tuned for RTX 5080.")

for exe in ["mace_run_train"]:
    path = shutil.which(exe)
    print(exe, path)
    if path is None:
        raise SystemExit(f"Missing executable: {exe}")

required = [
    "models/foundation/mace-mpa-0-medium.model",
    "models/finetuned_reference/li_mace_v1_3060ti.model",
    "models/finetuned_reference/li_mace_v1_3060ti.model-lammps.pt",
    "data/mace_datasets/li_mace_train.extxyz",
    "data/mace_datasets/li_mace_valid.extxyz",
    "data/mace_datasets/li_mace_test.extxyz",
]
required += [f"data/lammps/two_day_{case}_2x2x1.data" for case in [
    "A_Perfect", "B1_Monovacancy", "B2_Divacancy", "C_StoneWales", "D_SiGraphene"
]]
missing = [path for path in required if not Path(path).is_file()]
if missing:
    raise SystemExit("Missing required files:\n" + "\n".join(missing))
print("Required reviewer GPU inputs are present.")
PY

echo "Environment check passed."
