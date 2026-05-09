#!/usr/bin/env bash
#SBATCH -J vasp-SP_B2_Divacancy_path02_top_central_C_to_hollow_C3_img05
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=vasp-%j.out
#SBATCH --error=vasp-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge || true
module load vasp/5.4.1

cd "${SLURM_SUBMIT_DIR}"

ulimit -s unlimited
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export I_MPI_DEBUG="${I_MPI_DEBUG:-0}"

if [[ ! -s POTCAR ]]; then
    echo "Missing POTCAR in ${PWD}. Build it from licensed VASP PAW_PBE potentials." >&2
    exit 1
fi

which vasp_std
srun --mpi=pmi2 vasp_std > vasp.log
