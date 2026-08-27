#!/usr/bin/env bash
# Two-stage CPU-only PBE-D3(BJ)+dipole convergence workflow.

#SBATCH -J li-d3-conv
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

PROJECT_ROOT="${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}}"
JOB_LIST="${JOB_LIST:-${PROJECT_ROOT}/review_revision/d3_site_converged_jobs/job_list.txt}"
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
unset CUDA_VISIBLE_DEVICES

JOB_DIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${JOB_LIST}")"
if [[ -z "${JOB_DIR}" || ! -d "${JOB_DIR}" || ! -s "${JOB_DIR}/POTCAR" ]]; then
    echo "Invalid job directory for array index ${SLURM_ARRAY_TASK_ID}" >&2
    exit 1
fi
if [[ -f "${JOB_DIR}/SCF_CONVERGED" ]]; then
    echo "Already converged: ${JOB_DIR}"
    exit 0
fi
if [[ -e "${JOB_DIR}/OUTCAR" || -e "${JOB_DIR}/stage1" ]]; then
    echo "Refusing to overwrite prior outputs in ${JOB_DIR}" >&2
    exit 2
fi

VASP_BIN="$(command -v vasp_std || command -v vasp)"
unset I_MPI_PMI_LIBRARY
export I_MPI_PIN_RESPECT_CPUSET=0

final_iteration() {
    awk '
        $1 == "DAV:" || $1 == "RMM:" || $1 == "SDA:" ||
            $1 == "CGA:" || $1 == "CG:" || $1 == "DMP:" ||
            $1 == "DIA:" || $1 == "EIG:" {last=$2}
        $1 == "CG" && $2 == ":" {last=$3}
        END {print last+0}
    ' OSZICAR
}

run_stage() {
    local stage="$1"
    local nelm="$2"
    cp "INCAR.${stage}" INCAR
    mpirun -n "${SLURM_NTASKS}" "${VASP_BIN}" > "vasp_${stage}.log"
    if ! grep -q "General timing and accounting informations for this job" OUTCAR; then
        echo "${stage} did not complete" >&2
        exit 10
    fi
    if ! grep -q "aborting loop because EDIFF is reached" OUTCAR; then
        echo "${stage} did not reach EDIFF" >&2
        exit 11
    fi
    if grep -Eq "VERY BAD NEWS|BRMIX: very serious problems|ZBRENT: fatal error|Error EDDDAV|Call to ZHEGV failed" OUTCAR; then
        echo "${stage} contains a fatal electronic-structure marker" >&2
        exit 12
    fi
    local iteration
    iteration="$(final_iteration)"
    if (( iteration <= 0 || iteration >= nelm )); then
        echo "${stage} failed SCF gate: last_iter=${iteration} NELM=${nelm}" >&2
        exit 13
    fi
    echo "${stage} converged: last_iter=${iteration} NELM=${nelm}"
}

cd "${JOB_DIR}"
echo "CPU-only two-stage D3 calculation: ${JOB_DIR}"
echo "node=$(hostname) tasks=${SLURM_NTASKS} vasp=${VASP_BIN} launcher=mpirun"

run_stage stage1 180
mkdir stage1
cp INCAR OUTCAR OSZICAR CONTCAR vasp_stage1.log stage1/

rm -f OUTCAR OSZICAR CONTCAR DOSCAR EIGENVAL IBZKPT PCDAT REPORT XDATCAR \
    vasprun.xml
run_stage stage2 240
rm -f WAVECAR CHGCAR CHG
touch SCF_CONVERGED
