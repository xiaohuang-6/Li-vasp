#!/usr/bin/env bash
# Source this file to locate the local GPU LAMMPS-MACE runtime.

PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PACK_ROOT

if [[ -f "${PACK_ROOT}/local_runtime_env.sh" ]]; then
    # shellcheck disable=SC1091
    source "${PACK_ROOT}/local_runtime_env.sh"
elif [[ -f "${PACK_ROOT}/../local_3060ti_runpack/local_runtime_env.sh" ]]; then
    # shellcheck disable=SC1091
    source "${PACK_ROOT}/../local_3060ti_runpack/local_runtime_env.sh"
fi

find_lammps_bin() {
    local candidate
    for candidate in \
        "${LAMMPS_BIN:-}" \
        "${PACK_ROOT}/external/lammps-mace/build-local/install/bin/lmp" \
        "${PACK_ROOT}/external/lammps-mace/build-local/lmp" \
        "${PACK_ROOT}/../local_3060ti_runpack/external/lammps-mace/build-local/install/bin/lmp" \
        "${PACK_ROOT}/../local_3060ti_runpack/external/lammps-mace/build-local/lmp"; do
        if [[ -n "${candidate}" && -x "${candidate}" ]]; then
            echo "${candidate}"
            return 0
        fi
    done
    if command -v lmp >/dev/null 2>&1; then
        command -v lmp
        return 0
    fi
    return 1
}

find_libtorch_dir() {
    local candidate
    for candidate in \
        "${LIBTORCH_DIR:-}" \
        "${PACK_ROOT}/external/libtorch-gpu" \
        "${PACK_ROOT}/../local_3060ti_runpack/external/libtorch-gpu"; do
        if [[ -n "${candidate}" && -d "${candidate}/lib" ]]; then
            echo "${candidate}"
            return 0
        fi
    done
    return 1
}

if ! LAMMPS_BIN="$(find_lammps_bin)"; then
    echo "Could not find a GPU-capable LAMMPS binary." >&2
    echo "Set LAMMPS_BIN, or place this folder next to local_3060ti_runpack." >&2
    return 1 2>/dev/null || exit 1
fi
export LAMMPS_BIN

if LIBTORCH_DIR="$(find_libtorch_dir)"; then
    export LIBTORCH_DIR
    export LD_LIBRARY_PATH="${LIBTORCH_DIR}/lib:${LD_LIBRARY_PATH:-}"
fi

for libdir in \
    "$(dirname "$(dirname "${LAMMPS_BIN}")")/lib" \
    "$(dirname "${LAMMPS_BIN}")/../lib" \
    "${PACK_ROOT}/../local_3060ti_runpack/external/lammps-mace/build-local/install/lib" \
    "${PACK_ROOT}/../local_3060ti_runpack/external/lammps-mace/build-local"; do
    if [[ -d "${libdir}" ]]; then
        export LD_LIBRARY_PATH="${libdir}:${LD_LIBRARY_PATH:-}"
    fi
done

export DATA_FILE="${DATA_FILE:-${PACK_ROOT}/data/lammps/local_D_SiGraphene_2x2x1.data}"
export MACE_MODEL="${MACE_MODEL:-${PACK_ROOT}/models/li_mace_v1_3060ti.model-lammps.pt}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
