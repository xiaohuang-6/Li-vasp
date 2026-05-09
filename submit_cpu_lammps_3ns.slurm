#!/usr/bin/env bash
#SBATCH -J li-mace-cpu-3ns
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --exclusive
#SBATCH --mem=128G
#SBATCH --time=5-00:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
LAMMPS_BIN="${LAMMPS_BIN:-${PROJECT_ROOT}/external/lammps-mace-cpu/bin/lmp}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${PROJECT_ROOT}/external/libtorch-cpu}"

cd "${PROJECT_ROOT}"
mkdir -p logs trajectories lammps_logs restarts data/lammps

if ! type module >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
fi

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
    module load gcc/12.2.0 cmake/3.26.1 mpi/openmpi-3.1.4_gcc
fi

if [[ ! -x "${LAMMPS_BIN}" ]]; then
    echo "LAMMPS CPU binary is missing or not executable: ${LAMMPS_BIN}" >&2
    echo "Run submit_cpu_lammps_build.slurm first." >&2
    exit 1
fi

if [[ ! -f "data/lammps/local_D_SiGraphene_2x2x1.data" ]]; then
    echo "Missing LAMMPS data file: data/lammps/local_D_SiGraphene_2x2x1.data" >&2
    exit 1
fi

if [[ ! -f "local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model-lammps.pt" ]]; then
    echo "Missing MACE LAMMPS model." >&2
    exit 1
fi

export LD_LIBRARY_PATH="${PROJECT_ROOT}/external/lammps-mace-cpu/lib:${LIBTORCH_DIR}/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-64}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-64}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-64}"
export OMP_PROC_BIND=spread
export OMP_PLACES=cores

echo "Running 3 ns CPU MACE MD"
echo "LAMMPS_BIN=${LAMMPS_BIN}"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-unknown}"
echo "SLURM_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK:-unset}"
echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"
echo "MKL_NUM_THREADS=${MKL_NUM_THREADS}"
echo "Memory request: 128G"

"${LAMMPS_BIN}" -h | grep -i mace
mpirun -np "${SLURM_NTASKS:-1}" "${LAMMPS_BIN}" -in in.lammps_3ns_cpu
