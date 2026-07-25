#!/usr/bin/env bash
# Best-effort local build of ACEsuit LAMMPS-MACE for RTX 5080.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${ENV_NAME:-mace_review_5080}"
LMP_BRANCH="${LMP_BRANCH:-mace}"
JOBS="${JOBS:-$(nproc)}"
BUILD_DIR="${BUILD_DIR:-${ROOT}/external/lammps-mace/build-5080}"
INSTALL_DIR="${INSTALL_DIR:-${BUILD_DIR}/install}"

if ! command -v conda >/dev/null 2>&1; then
    echo "conda not found. Run environment/setup_mace_env_5080.sh first." >&2
    exit 1
fi
if ! command -v git >/dev/null 2>&1; then
    echo "git is required to clone ACEsuit/lammps." >&2
    exit 1
fi
if ! command -v cmake >/dev/null 2>&1; then
    echo "cmake is required. Install it with conda/pip/system package manager." >&2
    exit 1
fi
if ! command -v nvcc >/dev/null 2>&1; then
    echo "nvcc was not found. Install CUDA Toolkit 12.8+ for local LAMMPS GPU build." >&2
    exit 1
fi

CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

mkdir -p "${ROOT}/external"
if [[ ! -d "${ROOT}/external/lammps-mace/.git" ]]; then
    git clone --branch "${LMP_BRANCH}" --depth 1 https://github.com/ACEsuit/lammps.git "${ROOT}/external/lammps-mace"
fi

TORCH_PREFIX="$(python - <<'PY'
import torch
print(torch.utils.cmake_prefix_path)
PY
)"

ARCH_CANDIDATES=()
if [[ -n "${KOKKOS_ARCH:-}" ]]; then
    ARCH_CANDIDATES+=("${KOKKOS_ARCH}")
fi
ARCH_CANDIDATES+=(BLACKWELL120 BLACKWELL100 ADA89 AMPERE86)

for arch in "${ARCH_CANDIDATES[@]}"; do
    echo "Trying Kokkos architecture: ${arch}"
    rm -rf "${BUILD_DIR}"
    if cmake -S "${ROOT}/external/lammps-mace/cmake" -B "${BUILD_DIR}" \
        -D CMAKE_BUILD_TYPE=Release \
        -D CMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
        -D CMAKE_PREFIX_PATH="${TORCH_PREFIX}" \
        -D BUILD_MPI=ON \
        -D PKG_ML-MACE=ON \
        -D PKG_KOKKOS=ON \
        -D Kokkos_ENABLE_CUDA=ON \
        -D Kokkos_ENABLE_SERIAL=ON \
        -D "Kokkos_ARCH_${arch}=ON" \
        -D CMAKE_CUDA_ARCHITECTURES=120; then
        cmake --build "${BUILD_DIR}" -j "${JOBS}"
        cmake --install "${BUILD_DIR}"
        echo "Built LAMMPS-MACE: ${INSTALL_DIR}/bin/lmp"
        exit 0
    fi
done

echo "LAMMPS configure failed for all known Kokkos arch flags." >&2
echo "Set KOKKOS_ARCH manually after checking your LAMMPS/Kokkos version, then rerun." >&2
exit 1
