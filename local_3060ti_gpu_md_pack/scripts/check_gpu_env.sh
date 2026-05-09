#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

# shellcheck disable=SC1091
source scripts/env_gpu_lammps.sh

mkdir -p logs

echo "PACK_ROOT=${PACK_ROOT}"
echo "LAMMPS_BIN=${LAMMPS_BIN}"
echo "LIBTORCH_DIR=${LIBTORCH_DIR:-unset}"
echo "DATA_FILE=${DATA_FILE}"
echo "MACE_MODEL=${MACE_MODEL}"
echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"

if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi | tee logs/nvidia-smi.txt
else
    echo "nvidia-smi was not found in PATH." >&2
fi

"${LAMMPS_BIN}" -h | tee logs/lammps_help.txt | grep -i mace

echo "Environment check finished."
