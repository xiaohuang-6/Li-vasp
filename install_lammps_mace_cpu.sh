#!/usr/bin/env bash
# Build a CPU MPI LAMMPS binary with the ACEsuit ML-MACE package.
# Intended for et2024 CPU nodes. This avoids CUDA/KOKKOS so it can run small
# MACE smoke tests without occupying scarce GPU nodes.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
EXTERNAL_DIR="${EXTERNAL_DIR:-${PROJECT_ROOT}/external}"
LAMMPS_SRC="${LAMMPS_SRC:-${PROJECT_ROOT}/local_3060ti_runpack/external/lammps-mace}"
FALLBACK_LAMMPS_SRC="${EXTERNAL_DIR}/lammps-mace-cpu-src"
BUILD_DIR="${BUILD_DIR:-${EXTERNAL_DIR}/lammps-mace-cpu-build}"
INSTALL_PREFIX="${INSTALL_PREFIX:-${EXTERNAL_DIR}/lammps-mace-cpu}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${EXTERNAL_DIR}/libtorch-cpu}"
LIBTORCH_VERSION="${LIBTORCH_VERSION:-2.5.0}"
JOBS="${JOBS:-${SLURM_CPUS_PER_TASK:-8}}"
MODULE_LOADS="${MODULE_LOADS:-gcc/12.2.0 cmake/3.26.1 mpi/openmpi-3.1.4_gcc}"

export PATH="/usr/local/slurm/bin:${PATH}"

if ! type module >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
fi

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
    for module_name in ${MODULE_LOADS}; do
        module load "${module_name}"
    done
fi

mkdir -p "${EXTERNAL_DIR}"

if [[ ! -d "${LAMMPS_SRC}/src/ML-MACE" ]]; then
    LAMMPS_SRC="${FALLBACK_LAMMPS_SRC}"
    if [[ ! -d "${LAMMPS_SRC}/.git" ]]; then
        git clone --branch mace --depth=1 https://github.com/ACEsuit/lammps "${LAMMPS_SRC}"
    else
        git -C "${LAMMPS_SRC}" fetch --depth=1 origin mace
        git -C "${LAMMPS_SRC}" checkout mace
        git -C "${LAMMPS_SRC}" pull --ff-only origin mace
    fi
fi

if [[ ! -f "${LIBTORCH_DIR}/share/cmake/Torch/TorchConfig.cmake" ]]; then
    job_tag="${SLURM_JOB_ID:-$$}"
    tmp_zip="${EXTERNAL_DIR}/libtorch-${LIBTORCH_VERSION}-cpu.${job_tag}.zip"
    tmp_unpack="${EXTERNAL_DIR}/libtorch-cpu-unpack.${job_tag}"
    url="https://download.pytorch.org/libtorch/cpu/libtorch-shared-with-deps-${LIBTORCH_VERSION}%2Bcpu.zip"
    echo "Downloading CPU libtorch from ${url}"
    python -c 'import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], sys.argv[2])' "${url}" "${tmp_zip}"
    rm -rf "${tmp_unpack}"
    mkdir -p "${tmp_unpack}"
    unzip -q "${tmp_zip}" -d "${tmp_unpack}"
    rm -rf "${LIBTORCH_DIR}"
    mv "${tmp_unpack}/libtorch" "${LIBTORCH_DIR}"
    rm -rf "${tmp_unpack}" "${tmp_zip}"
fi

command -v cmake >/dev/null
command -v mpicxx >/dev/null

rm -rf "${BUILD_DIR}"
mkdir -p "${LIBTORCH_DIR}/include"

cmake -S "${LAMMPS_SRC}/cmake" -B "${BUILD_DIR}" \
    -D CMAKE_BUILD_TYPE=Release \
    -D CMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}" \
    -D CMAKE_CXX_STANDARD=17 \
    -D CMAKE_CXX_STANDARD_REQUIRED=ON \
    -D CMAKE_CXX_COMPILER=mpicxx \
    -D BUILD_MPI=ON \
    -D BUILD_SHARED_LIBS=ON \
    -D PKG_ML-MACE=ON \
    -D CMAKE_PREFIX_PATH="${LIBTORCH_DIR}" \
    -D MKL_INCLUDE_DIR="${LIBTORCH_DIR}/include" \
    -D MKL_ROOT="${LIBTORCH_DIR}" \
    -D CMAKE_INSTALL_RPATH="${INSTALL_PREFIX}/lib;${LIBTORCH_DIR}/lib"

cmake --build "${BUILD_DIR}" -j "${JOBS}"
cmake --install "${BUILD_DIR}"

export LD_LIBRARY_PATH="${INSTALL_PREFIX}/lib:${LIBTORCH_DIR}/lib:${LD_LIBRARY_PATH:-}"
"${INSTALL_PREFIX}/bin/lmp" -h | grep -i mace >/dev/null

echo "CPU LAMMPS-MACE binary is ready:"
echo "  ${INSTALL_PREFIX}/bin/lmp"
