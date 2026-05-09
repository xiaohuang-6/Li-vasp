#!/usr/bin/env bash
# Create the Python environment used by structure generation, MACE training, and
# model conversion. Run this once from the project root.
set -euo pipefail

ENV_NAME="${ENV_NAME:-mace_md}"
CONDA_BASE="${CONDA_BASE:-/home/xh121/anaconda3}"
TORCH_VERSION="${TORCH_VERSION:-2.5.0}"
CUDA_TAG="${CUDA_TAG:-cu121}"
INSTALL_CUEQ="${INSTALL_CUEQ:-0}"

if [[ ! -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]]; then
    echo "Cannot find conda.sh under ${CONDA_BASE}" >&2
    echo "Set CONDA_BASE to the directory returned by 'conda info --base'." >&2
    exit 1
fi

source "${CONDA_BASE}/etc/profile.d/conda.sh"

if ! conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    conda create -y -n "${ENV_NAME}" python=3.10
fi

conda activate "${ENV_NAME}"

python -m pip install --upgrade pip setuptools wheel

# Keep the Python torch wheel aligned with the libtorch CUDA family used by the
# LAMMPS build script. Override TORCH_VERSION/CUDA_TAG if your CUDA stack differs.
python -m pip install \
    "torch==${TORCH_VERSION}+${CUDA_TAG}" \
    --index-url "https://download.pytorch.org/whl/${CUDA_TAG}"

python -m pip install \
    ase \
    pymatgen \
    MDAnalysis \
    huggingface_hub \
    numpy \
    scipy \
    pandas \
    matplotlib \
    tqdm

python -m pip install "mace-torch @ git+https://github.com/ACEsuit/mace.git"

if [[ "${INSTALL_CUEQ}" == "1" ]]; then
    python -m pip install cuequivariance cuequivariance-torch "cupy-cuda12x"
    python -m pip install "cuequivariance-ops-torch-cu12"
fi

python - <<'PY'
import torch
print("Environment ready")
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
PY

echo "Activate with: conda activate ${ENV_NAME}"
