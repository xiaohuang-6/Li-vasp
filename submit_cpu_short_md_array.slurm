#!/usr/bin/env bash
#SBATCH -J li-rush-md10ps
#SBATCH -p et2_medmem,et3_medmem,et4_medmem,et2,et3,et4,et1_new
#SBATCH --array=0-4
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=18:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
LAMMPS_BIN="${LAMMPS_BIN:-${PROJECT_ROOT}/external/lammps-mace-cpu/bin/lmp}"
LIBTORCH_DIR="${LIBTORCH_DIR:-${PROJECT_ROOT}/external/libtorch-cpu}"
MODEL="${MODEL:-${PROJECT_ROOT}/local_3060ti_finetune_pack/models/local_finetuned_li_mace_v1/li_mace_v1_3060ti.model-lammps.pt}"
NSTEPS="${NSTEPS:-10000}"
TEMPERATURE="${TEMPERATURE:-400}"

CASES=(A_Perfect B1_Monovacancy B2_Divacancy C_StoneWales D_SiGraphene)
CASE="${CASES[${SLURM_ARRAY_TASK_ID}]}"
DATA_FILE="${PROJECT_ROOT}/data/lammps/two_day_${CASE}_2x2x1.data"

cd "${PROJECT_ROOT}"
mkdir -p logs trajectories/two_day_md lammps_logs/two_day_md restarts/two_day_md data/lammps

if ! type module >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
fi

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
    module load gcc/12.2.0 cmake/3.26.1 mpi/openmpi-3.1.4_gcc
fi

if [[ ! -x "${LAMMPS_BIN}" ]]; then
    echo "Missing LAMMPS binary: ${LAMMPS_BIN}" >&2
    exit 1
fi
if [[ ! -f "${MODEL}" ]]; then
    echo "Missing LAMMPS MACE model: ${MODEL}" >&2
    exit 1
fi
if [[ ! -f "${DATA_FILE}" ]]; then
    echo "Missing LAMMPS data file: ${DATA_FILE}" >&2
    echo "Run scripts_prepare_two_day_lammps_data.sh first." >&2
    exit 1
fi

export LD_LIBRARY_PATH="${PROJECT_ROOT}/external/lammps-mace-cpu/lib:${LIBTORCH_DIR}/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export OMP_PROC_BIND=spread
export OMP_PLACES=cores

echo "Running 10 ps CPU MACE MD"
echo "case=${CASE}"
echo "node=$(hostname)"
echo "nsteps=${NSTEPS}"
echo "temperature=${TEMPERATURE}"
echo "threads=${OMP_NUM_THREADS}"

"${LAMMPS_BIN}" -h | grep -i mace
"${LAMMPS_BIN}" \
    -var case "${CASE}" \
    -var data_file "${DATA_FILE}" \
    -var mace_model "${MODEL}" \
    -var temperature "${TEMPERATURE}" \
    -var nsteps "${NSTEPS}" \
    -var dump_every 100 \
    -in in.lammps_short_cpu
