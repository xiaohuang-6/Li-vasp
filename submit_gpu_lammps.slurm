#!/usr/bin/env bash
#SBATCH -J li-mace-md
#SBATCH -p et_gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${PROJECT_ROOT}/external/libtorch-gpu}"
LAMMPS_BIN="${LAMMPS_BIN:-${PROJECT_ROOT}/external/lammps-mace/build-gpu/install/bin/lmp}"

mkdir -p "${PROJECT_ROOT}/logs" "${PROJECT_ROOT}/trajectories"
cd "${PROJECT_ROOT}"

if [[ ! -x "${LAMMPS_BIN}" && -x "${PROJECT_ROOT}/external/lammps-mace/build-gpu/lmp" ]]; then
    LAMMPS_BIN="${PROJECT_ROOT}/external/lammps-mace/build-gpu/lmp"
fi
if [[ ! -x "${LAMMPS_BIN}" ]]; then
    echo "LAMMPS binary not found or not executable: ${LAMMPS_BIN}" >&2
    echo "Submit submit_gpu_install_lammps.slurm first or set LAMMPS_BIN." >&2
    exit 1
fi

export LD_LIBRARY_PATH="${LIBTORCH_DIR}/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"

mpirun -np 1 "$LAMMPS_BIN" -k on g 1 -sf kk -in in.lammps_diffusion
