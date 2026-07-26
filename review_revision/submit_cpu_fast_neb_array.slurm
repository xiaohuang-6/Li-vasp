#!/usr/bin/env bash
# Run low-cost CI-NEB fallback jobs for the 24h reviewer-revision push.
#
# Prepare:
#   cd /home/xh121/Li-vasp
#   conda activate mace_md
#   python review_revision/prepare_fast_neb_jobs.py --force
#
# Submit:
#   N=$(wc -l < review_revision/neb_fast_jobs/neb_fast_job_list.txt)
#   sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_fast_neb_array.slurm

#SBATCH -J li-fast-neb
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=24
#SBATCH --cpus-per-task=1
#SBATCH --mem=128G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
JOB_LIST="${JOB_LIST:-${PROJECT_ROOT}/review_revision/neb_fast_jobs/neb_fast_job_list.txt}"
VASP_MODULE="${VASP_MODULE:-vasp/5.4.1}"

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
    echo "Missing fast NEB job list: ${JOB_LIST}" >&2
    exit 1
fi

JOB_DIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${JOB_LIST}")"
if [[ -z "${JOB_DIR}" || ! -d "${JOB_DIR}" ]]; then
    echo "No job directory for array index ${SLURM_ARRAY_TASK_ID}" >&2
    exit 1
fi
if [[ ! -f "${JOB_DIR}/POTCAR" ]]; then
    echo "Missing ${JOB_DIR}/POTCAR" >&2
    exit 1
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
echo "Running fast NEB job in ${JOB_DIR}"
echo "node=$(hostname)"
echo "module=${VASP_MODULE}"
echo "vasp=${VASP_BIN}"

srun --mpi=pmi2 "${VASP_BIN}" > vasp.log
