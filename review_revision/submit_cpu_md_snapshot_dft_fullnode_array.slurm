#!/usr/bin/env bash
# High-parallelism alternative for VASP single-point checks of MD snapshots.
#
# Use this only for snapshot directories that are not already being written by
# an active Slurm job. The default uses a whole et2024 node.
#
# Example for all nine snapshot checks, one at a time:
#   sbatch --array=0-8%1 review_revision/submit_cpu_md_snapshot_dft_fullnode_array.slurm
#
# If deliberately restarting a directory that already contains vasp.log:
#   RESTART_EXISTING=1 sbatch --array=0 review_revision/submit_cpu_md_snapshot_dft_fullnode_array.slurm

#SBATCH -J li-md-dft64
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=64
#SBATCH --cpus-per-task=1
#SBATCH --mem=256G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
JOB_LIST="${JOB_LIST:-${PROJECT_ROOT}/review_revision/md_snapshot_dft_jobs/md_snapshot_dft_job_list.txt}"
VASP_MODULE="${VASP_MODULE:-vasp/5.4.1}"
RESTART_EXISTING="${RESTART_EXISTING:-0}"

cd "${PROJECT_ROOT}"
mkdir -p logs

source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge >/dev/null 2>&1 || true
module load "${VASP_MODULE}"

ulimit -s unlimited
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export I_MPI_DEBUG="${I_MPI_DEBUG:-0}"

if [[ ! -s "${JOB_LIST}" ]]; then
    echo "Missing MD snapshot DFT job list: ${JOB_LIST}" >&2
    exit 1
fi

JOB_DIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${JOB_LIST}")"
if [[ -z "${JOB_DIR}" || ! -d "${JOB_DIR}" ]]; then
    echo "No job directory for array index ${SLURM_ARRAY_TASK_ID}" >&2
    exit 1
fi
if [[ ! -f "${JOB_DIR}/POTCAR" ]]; then
    echo "Missing ${JOB_DIR}/POTCAR. See POTCAR_REQUIRED.txt if present." >&2
    exit 1
fi
if [[ -f "${JOB_DIR}/vasp.log" && "${RESTART_EXISTING}" != "1" ]]; then
    echo "${JOB_DIR}/vasp.log already exists." >&2
    echo "Refusing to overwrite a possibly active or partial snapshot check." >&2
    echo "Set RESTART_EXISTING=1 only after confirming no active job writes this directory." >&2
    exit 2
fi

if command -v vasp_std >/dev/null 2>&1; then
    VASP_BIN="$(command -v vasp_std)"
elif command -v vasp >/dev/null 2>&1; then
    VASP_BIN="$(command -v vasp)"
else
    echo "Could not find vasp_std or vasp after module load." >&2
    exit 1
fi

cd "${JOB_DIR}"
echo "Running full-node MD snapshot DFT check in ${JOB_DIR}"
echo "node=$(hostname)"
echo "module=${VASP_MODULE}"
echo "vasp=${VASP_BIN}"
echo "ntasks=${SLURM_NTASKS}"

srun --mpi=pmi2 "${VASP_BIN}" > vasp.log
