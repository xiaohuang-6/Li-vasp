#!/usr/bin/env bash
# Flexible CPU scaling test for the two-day MACE/LAMMPS rush workflow.
# This requests 32 cores on et2024 rather than an exclusive 64-core node,
# because current et2024 nodes are partially occupied but have 32-core gaps.
# The output decides whether to keep the existing 4-core MD jobs or relaunch
# the production short MD with more threads.
#SBATCH -J li-mace-scale32
#SBATCH -p et2024
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

set -euo pipefail
export PATH="/usr/local/slurm/bin:${PATH}"

PROJECT_ROOT="${PROJECT_ROOT:-/home/xh121/Li-vasp}"
cd "${PROJECT_ROOT}"
mkdir -p logs benchmarks

export DATA_FILE="${DATA_FILE:-${PROJECT_ROOT}/data/lammps/two_day_D_SiGraphene_2x2x1.data}"
export NSTEPS="${NSTEPS:-100}"
export THREAD_LIST="${THREAD_LIST:-1 2 4 8 16 32}"

bash scripts_cpu_scaling_benchmark.sh
