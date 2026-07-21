#!/usr/bin/env bash
# Submit prepared VASP CI-NEB templates on CPU nodes.
#
# Prepare first, for example:
#   conda activate mace_md
#   python review_revision/prepare_review_neb_jobs.py --potcar-root /path/to/potpaw_PBE
#
# Then submit:
#   sbatch --array=0-9 review_revision/submit_cpu_review_neb_array.slurm

#SBATCH -J li-review-neb
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=2-00:00:00
#SBATCH --output=logs/%x-%A_%a.out
#SBATCH --error=logs/%x-%A_%a.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
JOB_LIST="${JOB_LIST:-${PROJECT_ROOT}/review_revision/neb_jobs/neb_job_list.txt}"

cd "${PROJECT_ROOT}"
mkdir -p logs

if type module >/dev/null 2>&1; then
    module purge >/dev/null 2>&1 || true
    module load vasp/5.4.1 >/dev/null 2>&1 || module load vasp/5.4.1.VASPsol >/dev/null 2>&1 || true
fi

if [[ ! -s "${JOB_LIST}" ]]; then
    echo "Missing NEB job list: ${JOB_LIST}" >&2
    echo "Run review_revision/prepare_review_neb_jobs.py first." >&2
    exit 1
fi

JOB_DIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${JOB_LIST}")"
if [[ -z "${JOB_DIR}" || ! -d "${JOB_DIR}" ]]; then
    echo "No job directory for array index ${SLURM_ARRAY_TASK_ID}" >&2
    exit 1
fi
if [[ ! -f "${JOB_DIR}/POTCAR" ]]; then
    echo "Missing ${JOB_DIR}/POTCAR. See POTCAR_REQUIRED.txt." >&2
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
echo "Running NEB job in ${JOB_DIR}"
echo "node=$(hostname)"
echo "vasp=${VASP_BIN}"

srun "${VASP_BIN}" > vasp.log
