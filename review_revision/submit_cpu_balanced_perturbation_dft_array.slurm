#!/usr/bin/env bash
# CPU-only VASP array for the family-balanced perturbation benchmark.

#SBATCH -J li-bal-force
#SBATCH -p et3
#SBATCH --nodes=1
#SBATCH --ntasks=20
#SBATCH --cpus-per-task=1
#SBATCH --mem=28G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}}"
JOB_LIST="${JOB_LIST:-${PROJECT_ROOT}/review_revision/balanced_perturbation_dft_jobs/job_list.txt}"
VASP_MODULE="${VASP_MODULE:-vasp/5.4.1}"
MPI_LAUNCHER="${MPI_LAUNCHER:-mpirun}"

cd "${PROJECT_ROOT}"
mkdir -p logs
source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge >/dev/null 2>&1 || true
module load "${VASP_MODULE}"

ulimit -s unlimited
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

JOB_DIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${JOB_LIST}")"
if [[ -z "${JOB_DIR}" || ! -d "${JOB_DIR}" ]]; then
    echo "Invalid array index ${SLURM_ARRAY_TASK_ID}" >&2
    exit 1
fi
if [[ ! -s "${JOB_DIR}/POTCAR" ]]; then
    echo "Missing POTCAR in ${JOB_DIR}" >&2
    exit 1
fi
if grep -q "General timing and accounting informations for this job" "${JOB_DIR}/OUTCAR" 2>/dev/null; then
    echo "Already complete: ${JOB_DIR}"
    exit 0
fi
if [[ -s "${JOB_DIR}/OUTCAR" ]]; then
    echo "Refusing to overwrite partial OUTCAR in ${JOB_DIR}" >&2
    exit 2
fi

VASP_BIN="$(command -v vasp_std || command -v vasp)"
cd "${JOB_DIR}"
echo "CPU-only balanced force benchmark: ${JOB_DIR}"
echo "node=$(hostname) tasks=${SLURM_NTASKS} vasp=${VASP_BIN} launcher=${MPI_LAUNCHER}"

case "${MPI_LAUNCHER}" in
    mpirun)
        # Intel MPI detects the Slurm allocation through Hydra. This path is
        # required on et3, where direct PMI-2 launch is incompatible.
        unset I_MPI_PMI_LIBRARY
        export I_MPI_PIN_RESPECT_CPUSET=0
        mpirun -n "${SLURM_NTASKS}" "${VASP_BIN}" > vasp.log
        ;;
    srun)
        srun --mpi=pmi2 "${VASP_BIN}" > vasp.log
        ;;
    *)
        echo "Unsupported MPI_LAUNCHER=${MPI_LAUNCHER}" >&2
        exit 3
        ;;
esac
