#!/usr/bin/env bash
#SBATCH -J li-mace-cpu-smoke
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
LAMMPS_BIN="${LAMMPS_BIN:-${PROJECT_ROOT}/external/lammps-mace-cpu/bin/lmp}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${PROJECT_ROOT}/external/libtorch-cpu}"

cd "${PROJECT_ROOT}"
mkdir -p logs trajectories lammps_logs

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
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"

"${LAMMPS_BIN}" -h | grep -i mace
mpirun -np "${SLURM_NTASKS:-1}" "${LAMMPS_BIN}" -in in.lammps_smoke_cpu
