#!/usr/bin/env bash
#SBATCH -J li-mace-lmp-build
#SBATCH -p et_gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
mkdir -p "${PROJECT_ROOT}/logs"
cd "${PROJECT_ROOT}"

bash install_lammps_mace_gpu.sh
