#!/usr/bin/env bash
#SBATCH -J li-mace-cpu-scale
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --exclusive
#SBATCH --mem=128G
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
cd "${PROJECT_ROOT}"
mkdir -p logs benchmarks

export NSTEPS="${NSTEPS:-100}"
export THREAD_LIST="${THREAD_LIST:-1 2 4 8 16 32 64}"

bash scripts_cpu_scaling_benchmark.sh
