#!/usr/bin/env bash
#SBATCH -J li-mace-prep
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
CONDA_BASE="${CONDA_BASE:-/home/xh121/anaconda3}"
ENV_NAME="${ENV_NAME:-mace_md}"

mkdir -p "${PROJECT_ROOT}/logs"
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"
cd "${PROJECT_ROOT}"

python build_defect_structures.py

shopt -s globstar nullglob
outcars=(dft_outputs/**/OUTCAR)
if (( ${#outcars[@]} > 0 )); then
    python vasp_to_extxyz.py --input-glob "dft_outputs/**/OUTCAR" --output data/train_data.extxyz
else
    echo "No dft_outputs/**/OUTCAR files found; skipping extxyz conversion."
fi

if [[ -s structures/optimized/CONTCAR ]]; then
    python build_lammps_data.py --input structures/optimized/CONTCAR --output data/lammps/defective_graphene.data
else
    echo "No structures/optimized/CONTCAR found; skipping LAMMPS data generation."
fi
