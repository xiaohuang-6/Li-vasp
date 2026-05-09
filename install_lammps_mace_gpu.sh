#!/usr/bin/env bash
# Build the ACEsuit LAMMPS branch with ML-MACE, KOKKOS CUDA, and libtorch.
# Run this on the et_gpu partition, not on the login node.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
EXTERNAL_DIR="${EXTERNAL_DIR:-${PROJECT_ROOT}/external}"
LAMMPS_DIR="${LAMMPS_DIR:-${EXTERNAL_DIR}/lammps-mace}"
BUILD_DIR="${BUILD_DIR:-${LAMMPS_DIR}/build-gpu}"
INSTALL_PREFIX="${INSTALL_PREFIX:-${BUILD_DIR}/install}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${EXTERNAL_DIR}/libtorch-gpu}"
LIBTORCH_VERSION="${LIBTORCH_VERSION:-2.5.0}"
CUDA_TAG="${CUDA_TAG:-cu121}"
JOBS="${JOBS:-20}"
MODULE_PURGE="${MODULE_PURGE:-0}"
MODULE_LOADS="${MODULE_LOADS:-gcc/12.2.0 mpi/openmpi-4.1.1_gcc cmake/3.26.1}"

export PATH="/usr/local/slurm/bin:${PATH}"

if ! type module >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
fi

if type module >/dev/null 2>&1; then
    if [[ "${MODULE_PURGE}" == "1" ]]; then
        module purge
    fi
    for module_name in ${MODULE_LOADS}; do
        module load "${module_name}" || true
    done
fi

if ! command -v git >/dev/null 2>&1; then
    echo "git is required to clone ACEsuit/lammps" >&2
    exit 1
fi
if ! command -v cmake >/dev/null 2>&1; then
    echo "cmake is required. Load cmake/3.26.1 or set MODULE_LOADS." >&2
    exit 1
fi
if ! command -v nvcc >/dev/null 2>&1; then
    echo "nvcc was not found. Run on a CUDA GPU node or load the CUDA module." >&2
    exit 1
fi

mkdir -p "${EXTERNAL_DIR}"

if [[ ! -d "${LAMMPS_DIR}/.git" ]]; then
    git clone --branch mace --depth=1 https://github.com/ACEsuit/lammps "${LAMMPS_DIR}"
else
    git -C "${LAMMPS_DIR}" fetch --depth=1 origin mace
    git -C "${LAMMPS_DIR}" checkout mace
    git -C "${LAMMPS_DIR}" pull --ff-only origin mace
fi

if [[ ! -d "${LIBTORCH_DIR}/lib" ]]; then
    tmp_zip="${EXTERNAL_DIR}/libtorch-${LIBTORCH_VERSION}-${CUDA_TAG}.zip"
    url="https://download.pytorch.org/libtorch/${CUDA_TAG}/libtorch-shared-with-deps-${LIBTORCH_VERSION}%2B${CUDA_TAG}.zip"
    echo "Downloading ${url}"
    python - <<PY
import urllib.request
urllib.request.urlretrieve("${url}", "${tmp_zip}")
PY
    rm -rf "${EXTERNAL_DIR}/libtorch" "${LIBTORCH_DIR}"
    unzip -q "${tmp_zip}" -d "${EXTERNAL_DIR}"
    mv "${EXTERNAL_DIR}/libtorch" "${LIBTORCH_DIR}"
fi

detect_kokkos_arch() {
    if [[ -n "${KOKKOS_ARCH_FLAG:-}" ]]; then
        echo "${KOKKOS_ARCH_FLAG}"
        return
    fi
    for flag in Kokkos_ARCH_AMPERE80 Kokkos_ARCH_AMPERE100; do
        if grep -R "${flag}" "${LAMMPS_DIR}/lib/kokkos" "${LAMMPS_DIR}/cmake" >/dev/null 2>&1; then
            echo "${flag}"
            return
        fi
    done
    echo "Kokkos_ARCH_AMPERE80"
}

KOKKOS_ARCH_FLAG="$(detect_kokkos_arch)"
NVCC_WRAPPER="${LAMMPS_DIR}/lib/kokkos/bin/nvcc_wrapper"
if [[ ! -x "${NVCC_WRAPPER}" ]]; then
    echo "Kokkos nvcc_wrapper not found: ${NVCC_WRAPPER}" >&2
    exit 1
fi

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

cmake \
    -D CMAKE_BUILD_TYPE=Release \
    -D CMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}" \
    -D CMAKE_CXX_STANDARD=17 \
    -D CMAKE_CXX_STANDARD_REQUIRED=ON \
    -D BUILD_MPI=ON \
    -D BUILD_SHARED_LIBS=ON \
    -D PKG_KOKKOS=ON \
    -D Kokkos_ENABLE_CUDA=ON \
    -D "${KOKKOS_ARCH_FLAG}=ON" \
    -D CMAKE_CXX_COMPILER="${NVCC_WRAPPER}" \
    -D CMAKE_PREFIX_PATH="${LIBTORCH_DIR}" \
    -D PKG_ML-MACE=ON \
    ../cmake

cmake --build . -j "${JOBS}"
cmake --install .

echo "LAMMPS binary: ${INSTALL_PREFIX}/bin/lmp"
"${INSTALL_PREFIX}/bin/lmp" -h | grep -i mace || {
    echo "Built LAMMPS, but pair_style mace was not found in lmp -h output." >&2
    exit 1
}
