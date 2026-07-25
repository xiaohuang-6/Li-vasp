#!/usr/bin/env bash
# Run VASP single-point checks for selected high-displacement MD snapshots.
#
# Prepare first:
#   cd /home/xh121/Li-vasp
#   conda activate mace_md
#   python review_revision/prepare_md_snapshot_dft_checks.py --top-runs 3 --snapshots-per-run 2 --also-final
#
# Submit:
#   N=$(wc -l < review_revision/md_snapshot_dft_jobs/md_snapshot_dft_job_list.txt)
#   sbatch --array=0-$((N-1))%2 review_revision/submit_cpu_md_snapshot_dft_array.slurm

#SBATCH -J li-md-dftcheck
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --mem=96G
#SBATCH --time=1-00:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
JOB_LIST="${JOB_LIST:-${PROJECT_ROOT}/review_revision/md_snapshot_dft_jobs/md_snapshot_dft_job_list.txt}"
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
    echo "Missing MD snapshot DFT job list: ${JOB_LIST}" >&2
    echo "Run review_revision/prepare_md_snapshot_dft_checks.py first." >&2
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

if command -v vasp_std >/dev/null 2>&1; then
    VASP_BIN="$(command -v vasp_std)"
elif command -v vasp >/dev/null 2>&1; then
    VASP_BIN="$(command -v vasp)"
else
    echo "Could not find vasp_std or vasp after module load." >&2
    exit 1
fi

cd "${JOB_DIR}"
echo "Running MD snapshot DFT check in ${JOB_DIR}"
echo "node=$(hostname)"
echo "module=${VASP_MODULE}"
echo "vasp=${VASP_BIN}"

srun --mpi=pmi2 "${VASP_BIN}" > vasp.log
