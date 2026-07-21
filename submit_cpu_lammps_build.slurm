#!/usr/bin/env bash
#SBATCH -J li-mace-cpu-build
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
cd "${PROJECT_ROOT}"
mkdir -p logs external

export JOBS="${SLURM_CPUS_PER_TASK:-8}"
bash install_lammps_mace_cpu.sh
