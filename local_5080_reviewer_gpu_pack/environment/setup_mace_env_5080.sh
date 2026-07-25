#!/usr/bin/env bash
# Create a local Python/MACE environment for RTX 5080 reviewer GPU tasks.
set -euo pipefail

ENV_NAME="${ENV_NAME:-mace_review_5080}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
PYTORCH_INDEX_URL="${PYTORCH_INDEX_URL:-https://download.pytorch.org/whl/cu128}"

if ! command -v conda >/dev/null 2>&1; then
    echo "conda was not found on PATH. Install Miniforge/Miniconda first, then rerun this script." >&2
    exit 1
fi

CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"

if ! conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    conda create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}"
fi

conda activate "${ENV_NAME}"
python -m pip install --upgrade pip setuptools wheel

# RTX 5080 is Blackwell / compute capability 12.0, so use CUDA 12.8+ PyTorch wheels.
python -m pip install --upgrade torch torchvision torchaudio --index-url "${PYTORCH_INDEX_URL}"

python -m pip install --upgrade \
    ase pymatgen MDAnalysis pandas numpy scipy matplotlib tqdm pyyaml

python -m pip install --upgrade "git+https://github.com/ACEsuit/mace.git"

python - <<'PY'
import shutil
import sys
import torch

print("python:", sys.version)
print("torch:", torch.__version__)
print("torch cuda:", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))
    print("capability:", torch.cuda.get_device_capability(0))
else:
    raise SystemExit("PyTorch cannot see CUDA. Check NVIDIA driver and CUDA-compatible PyTorch wheel.")

if shutil.which("mace_run_train") is None:
    raise SystemExit("mace_run_train is not on PATH after installing mace.")
print("mace_run_train:", shutil.which("mace_run_train"))
PY

echo "Environment ready: ${ENV_NAME}"
